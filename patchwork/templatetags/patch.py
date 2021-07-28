# Patchwork - automated patch tracking system
# Copyright (C) 2008 Jeremy Kerr <jk@ozlabs.org>
# Copyright (C) 2015 Intel Corporation
#
# SPDX-License-Identifier: GPL-2.0-or-later

from django import template
from django.utils.html import escape
from django.utils.safestring import mark_safe

from patchwork.models import Check


register = template.Library()


@register.filter(name='patch_tags')
def patch_tags(patch):
    counts, titles = patch.patch_tags_count()
    return mark_safe('<span title="%s">%s</span>' % (
        ' / '.join(titles),
        ' '.join([str(x) for x in counts])))


@register.filter(name='patch_relation_tags')
def patch_relation_tags(related_patches, project):
    tags = [tag.abbrev for tag in project.tags]
    tags_summary = ["-" for _ in range(len(tags))]
    for patch in related_patches:
        counts = patch.patch_tags_count()[0]
        for i, count in enumerate(counts):
            if count != '-':
                # Replaces a non-zero tag count with tag abbreviation
                # to indicate that existence of such tag in the set
                # of related patches
                tags_summary[i] = tags[i]
    return mark_safe('<span>%s</span>' % (' '.join(tags_summary)))


@register.filter(name='patch_checks')
def patch_checks(patch):
    required = [Check.STATE_SUCCESS, Check.STATE_WARNING, Check.STATE_FAIL]
    titles = ['Success', 'Warning', 'Fail']
    counts = patch.check_count

    check_elements = []
    use_color = True
    for state in required[::-1]:
        if counts[state]:
            if use_color:
                use_color = False
                color = dict(Check.STATE_CHOICES).get(state)
            else:
                color = ''
            count = str(counts[state])
        else:
            color = ''
            count = '-'

        check_elements.append(
            '<span class="patchlistchecks {}">{}</span>'.format(
                color, count))

    check_elements.reverse()

    return mark_safe('<span title="%s">%s</span>' % (
        ' / '.join(titles),
        ''.join(check_elements)))


@register.filter(name='patch_commit_display')
def patch_commit_display(patch):
    commit = patch.commit_ref
    fmt = patch.project.commit_url_format

    if not fmt:
        return escape(commit)

    return mark_safe('<a href="%s">%s</a>' % (escape(fmt.format(commit)),
                                              escape(commit)))


# TODO: can be modularized into a utils.py templatetags file
# to get is_editable from any object
@register.filter(name='patch_is_editable')
def patch_is_editable(patch, user):
    return patch.is_editable(user)
