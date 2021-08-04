# Patchwork - automated patch tracking system
# Copyright (C) 2008 Jeremy Kerr <jk@ozlabs.org>
#
# SPDX-License-Identifier: GPL-2.0-or-later

from django.contrib import messages
from django.http import Http404
from django.http import HttpResponse
from django.http import HttpResponseForbidden
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.shortcuts import render
from django.urls import reverse

from patchwork.forms import CreateBundleForm
from patchwork.forms import PatchForm
from patchwork.models import Cover
from patchwork.models import Patch
from patchwork.models import Project
from patchwork.views import generic_list
from patchwork.views import set_bundle
from patchwork.views import get_patch_relations_data
from patchwork.views.utils import patch_to_mbox
from patchwork.views.utils import series_patch_to_mbox
from patchwork.api.patch import update_patch_relations


def patch_list(request, project_id):
    project = get_object_or_404(Project, linkname=project_id)
    context = generic_list(request, project, 'patch-list',
                           view_args={'project_id': project.linkname})

    if request.user.is_authenticated:
        context['bundles'] = request.user.bundles.all()

    return render(request, 'patchwork/list.html', context)


def patch_detail(request, project_id, msgid):
    project = get_object_or_404(Project, linkname=project_id)
    db_msgid = ('<%s>' % msgid)

    # redirect to cover letters where necessary
    try:
        # Current patch needs tag counts when no relation exists
        patch_qs = Patch.objects.filter(
            project_id=project.id, msgid=db_msgid
        ).with_tag_counts(project)
        patch = patch_qs.get()
    except Patch.DoesNotExist:
        covers = Cover.objects.filter(
            project_id=project.id,
            msgid=db_msgid,
        )
        if covers:
            return HttpResponseRedirect(
                reverse('cover-detail',
                        kwargs={'project_id': project.linkname,
                                'msgid': msgid}))
        raise Http404('Patch does not exist')

    editable = patch.is_editable(request.user)
    context = {
        'project': patch.project
    }

    form = None
    createbundleform = None
    errors = []

    if editable:
        form = PatchForm(instance=patch)
    if request.user.is_authenticated:
        createbundleform = CreateBundleForm()

    if request.method == 'POST':
        action = request.POST.get('action', None)
        if action:
            action = action.lower()

        if action in ['create', 'add']:
            errors = set_bundle(request, project, action,
                                request.POST, [patch])
        elif action in ('add-related', 'remove-related'):
            changed_relations = 0  # used for update message count
            data, invalid_ids = get_patch_relations_data(
                patch, action, request.POST
            )

            if data['related']['patches']:  # check if any ids matched
                if action == 'add-related':
                    update_errors = update_patch_relations(
                        request.user.profile, patch, data
                    )
                    errors.extend(update_errors)
                    if not update_errors:
                        changed_relations += 1
                elif action == 'remove-related':
                    for rp in data['related']['patches']:
                        # for removal, to-be removed patch(es)'
                        # relations are emptied
                        update_errors = update_patch_relations(
                            request.user.profile, rp,
                            {'related': {'patches': []}}
                        )
                        errors.extend(update_errors)
                        if not update_errors:
                            changed_relations += 1

            errors.extend(
                ['%s is not a valid patch/msg id' % pid for pid in invalid_ids]
            )
            if changed_relations >= 1:
                messages.success(
                    request,
                    '%d patch relation(s) updated' % changed_relations
                )
            else:
                messages.warning(request, 'No patch relations updated')

        # all other actions require edit privs
        elif not editable:
            return HttpResponseForbidden()

        elif action == 'update':
            form = PatchForm(data=request.POST, instance=patch)
            if form.is_valid():
                form.save()
                messages.success(request, 'Patch updated')

    if request.user.is_authenticated:
        context['bundles'] = request.user.bundles.all()

    comments = patch.comments.all()
    comments = comments.select_related('submitter')
    comments = comments.only('submitter', 'date', 'id', 'content', 'patch',
                             'addressed')

    if patch.related:
        related_same_project = patch.related.patches.order_by('-id').only(
            'name', 'msgid', 'project', 'related').with_tag_counts(project)
        related_ids = {'ids': [rp.id for rp in related_same_project]}
        # avoid a second trip out to the db for info we already have
        related_different_project = [
            related_patch for related_patch in related_same_project
            if related_patch.project_id != patch.project_id
        ]
    else:
        # If no patch relation exists, then current patch is only related.
        # Add tag counts to the patch to display in patch relation table.
        related_same_project = [patch]
        related_ids = {'ids': [patch.id]}
        related_different_project = []

    context['comments'] = comments
    context['checks'] = Patch.filter_unique_checks(
        patch.check_set.all().select_related('user'),
    )
    context['submission'] = patch
    context['editable'] = editable
    context['patchform'] = form
    context['createbundleform'] = createbundleform
    context['project'] = patch.project
    context['patch_relation'] = patch.related
    context['related_same_project'] = related_same_project
    context['related_ids'] = related_ids
    context['related_different_project'] = related_different_project
    context['errors'] = errors

    return render(request, 'patchwork/submission.html', context)


def patch_raw(request, project_id, msgid):
    db_msgid = ('<%s>' % msgid)
    project = get_object_or_404(Project, linkname=project_id)
    patch = get_object_or_404(Patch, project_id=project.id, msgid=db_msgid)

    response = HttpResponse(content_type="text/x-patch")
    response.write(patch.diff)
    response['Content-Disposition'] = 'attachment; filename=%s.diff' % (
        patch.filename)

    return response


def patch_mbox(request, project_id, msgid):
    db_msgid = ('<%s>' % msgid)
    project = get_object_or_404(Project, linkname=project_id)
    patch = get_object_or_404(Patch, project_id=project.id, msgid=db_msgid)
    series_id = request.GET.get('series')

    response = HttpResponse(content_type='text/plain; charset=utf-8')
    if series_id:
        response.write(series_patch_to_mbox(patch, series_id))
    else:
        response.write(patch_to_mbox(patch))
    response['Content-Disposition'] = 'attachment; filename=%s.patch' % (
        patch.filename)

    return response


def patch_by_id(request, patch_id):
    patch = get_object_or_404(Patch, id=patch_id)

    url = reverse('patch-detail', kwargs={'project_id': patch.project.linkname,
                                          'msgid': patch.url_msgid})

    return HttpResponseRedirect(url)


def patch_mbox_by_id(request, patch_id):
    patch = get_object_or_404(Patch, id=patch_id)

    url = reverse('patch-mbox', kwargs={'project_id': patch.project.linkname,
                                        'msgid': patch.url_msgid})

    return HttpResponseRedirect(url)


def patch_raw_by_id(request, patch_id):
    patch = get_object_or_404(Patch, id=patch_id)

    url = reverse('patch-raw', kwargs={'project_id': patch.project.linkname,
                                       'msgid': patch.url_msgid})

    return HttpResponseRedirect(url)
