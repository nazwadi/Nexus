from django.conf import settings
from django.http import Http404
from django.shortcuts import render
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import F, Q
from django.views.decorators.http import require_http_methods

from common.models.spells import SpellsNew
from common.models.items import Items
from spells.models import SpellExpansion, SpellPatchHistory, SpellScroll
from spells.utils import calc_buff_duration, CASTING_CLASS_IDS, get_class_spell_list, prep_spell_data


@require_http_methods(["GET"])
def index(request):
    """
    Defines view for https://url.tld/spells/

    This index allows selecting spell quick list and vendor lists by class

    :param request: Http request
    :return: an Http Response object
    """
    return render(request=request,
                  template_name="spells/spells_index.html",
                  context={},
                  )


@require_http_methods(["GET", "POST"])
def search(request):
    """
    Search for a spell by name at https://url.tld/spells/search

    :param request: Http request
    :return: Http response
    """
    classes = {
        1: "Warrior",
        2: "Cleric",
        3: "Paladin",
        4: "Ranger",
        5: "Shadowknight",
        6: "Druid",
        7: "Monk",
        8: "Bard",
        9: "Rogue",
        10: "Shaman",
        11: "Necromancer",
        12: "Wizard",
        13: "Magician",
        14: "Enchanter",
        15: "Beastlord",
    }
    if request.method == "GET":
        return render(request=request,
                      template_name="spells/search_spells.html",
                      context={"classes": classes},
                      )
    if request.method == "POST":
        spell_name = request.POST.get("spell_name")
        class_name = request.POST.get("class_name")
        level = request.POST.get("level")
        if class_name == "Warrior":
            spell_results = SpellsNew.objects.filter(name__icontains=spell_name).filter(~Q(classes1__lte=255))
        elif class_name == "Cleric":
            spell_results = SpellsNew.objects.filter(name__icontains=spell_name).filter(~Q(classes2=255))
        elif class_name == "Paladin":
            spell_results = SpellsNew.objects.filter(name__icontains=spell_name).filter(~Q(classes3__lte=255))
        elif class_name == "Ranger":
            spell_results = SpellsNew.objects.filter(name__icontains=spell_name).filter(~Q(classes4__lte=255))
        elif class_name == "Shadowknight":
            spell_results = SpellsNew.objects.filter(name__icontains=spell_name).filter(~Q(classes5__lte=255))
        elif class_name == "Druid":
            spell_results = SpellsNew.objects.filter(name__icontains=spell_name).filter(~Q(classes6__lte=255))
        elif class_name == "Monk":
            spell_results = SpellsNew.objects.filter(name__icontains=spell_name).filter(~Q(classes7__lte=255))
        elif class_name == "Bard":
            spell_results = SpellsNew.objects.filter(name__icontains=spell_name).filter(~Q(classes8__lte=255))
        elif class_name == "Rogue":
            spell_results = SpellsNew.objects.filter(name__icontains=spell_name).filter(~Q(classes9__lte=255))
        elif class_name == "Shaman":
            spell_results = SpellsNew.objects.filter(name__icontains=spell_name).filter(~Q(classes10__lte=255))
        elif class_name == "Necromancer":
            spell_results = SpellsNew.objects.filter(name__icontains=spell_name).filter(~Q(classes11__lte=255))
        elif class_name == "Wizard":
            spell_results = SpellsNew.objects.filter(name__icontains=spell_name).filter(~Q(classes12__lte=255))
        elif class_name == "Magician":
            spell_results = SpellsNew.objects.filter(name__icontains=spell_name).filter(~Q(classes13__lte=255))
        elif class_name == "Enchanter":
            spell_results = SpellsNew.objects.filter(name__icontains=spell_name).filter(~Q(classes14__lte=255))
        elif class_name == "Beastlord":
            spell_results = SpellsNew.objects.filter(name__icontains=spell_name).filter(~Q(classes15__lte=255))
        elif class_name == "Berserker":
            spell_results = SpellsNew.objects.filter(name__icontains=spell_name).filter(~Q(classes16__lte=255))
        else:
            spell_results = SpellsNew.objects.filter(name__icontains=spell_name)

        return render(request=request,
                      template_name="spells/search_spells.html",
                      context={
                          "classes": classes,
                          "spell_results": spell_results,
                      },
                      )


@require_http_methods(["GET"])
def list_spells(request, class_id):
    """
    Defines view for https://url.tld/spells/list/<int:pk>

    :param request: Http request
    :param class_id: a class id field unique identifier
    :return: Http response
    """
    if class_id not in CASTING_CLASS_IDS:
        raise Http404("That class does not cast spells.")

    spell_list = get_class_spell_list(class_id)

    return render(request=request,
                  template_name="spells/list.html",
                  context={
                      "class_id": class_id,
                      "spell_list": spell_list,
                      "character_spells": [],
                      "expansion_choices": SpellExpansion.EXPANSION_CHOICES,
                      "server_expansion": settings.SERVER_EXPANSION,
                      "server_max_level": settings.SERVER_MAX_LEVEL,
                  })


@require_http_methods(["GET"])
def buy_spells(request, class_id):
    """
    Defines view for https://url.tld/spells/buy/<int:pk>

    :param request: Http request
    :param class_id: a class id field unique identifier
    :return: Http response
    """
    clsid = class_id if class_id in [2, 3, 4, 5, 6, 8, 10, 11, 12, 13, 14, 15] else None
    if clsid is None:
        raise Http404("Sorry, that class id doesn't exist, or the class doesn't cast spells.")

    level_field = f'classes{clsid}'

    # Spell IDs valid for this class + their class-specific level
    spell_level_map = {
        row['id']: row[level_field]
        for row in SpellsNew.objects.filter(
            **{f'{level_field}__lt': 255}
        ).values('id', level_field)
    }

    # Restrict to scrolls within the current expansion
    valid_spell_ids = set(
        SpellExpansion.objects.filter(
            id__in=spell_level_map.keys(),
            expansion__lte=SpellExpansion.MAX_EXPANSION,
        ).values_list('id', flat=True)
    )

    scrolls = (
        SpellScroll.objects
        .filter(spell_id__in=valid_spell_ids)
        .prefetch_related('vendors')
    )

    spells = []
    for scroll in scrolls:
        vendors_by_zone = {}
        for v in scroll.vendors.all():
            vendors_by_zone.setdefault(v.zone_long_name, []).append(
                {'id': v.merchant_id, 'info': v.merchant_name}
            )
        spells.append({
            'id': scroll.spell_id,
            'name': scroll.spell_name,
            'item_id': scroll.scroll_item_id,
            'item_name': scroll.scroll_item_name,
            'item_price': scroll.scroll_price,
            'item_rate': scroll.scroll_rate,
            'new_icon': scroll.icon,
            'level': spell_level_map.get(scroll.spell_id, 0),
            'purchase_location_info': vendors_by_zone or 'None',
        })

    spells.sort(key=lambda s: s['level'])

    return render(request=request,
                  template_name="spells/buy.html",
                  context={"class_id": str(clsid), "spells": spells},
                  )


@require_http_methods(["GET"])
def view_spell(request, spell_id):
    """
    Defines view for https://url.tld/spells/view/<int:pk>

    :param request: Http request
    :param spell_id: a spell id field unique identifier
    :return: Http response
    """
    try:
        spell_data = SpellsNew.objects.get(pk=spell_id)
    except ObjectDoesNotExist:
        raise Http404("Sorry, that spell doesn't exist.")
    else:
        min_level = 65
        spell_min_duration = calc_buff_duration(min_level, spell_data.buff_duration_formula, spell_data.buff_duration)
        spell_min_time = spell_min_duration * 6
        spell_max_duration = calc_buff_duration(65, spell_data.buff_duration_formula, spell_data.buff_duration)
        spell_max_time = spell_max_duration * 6

        sp_effects = prep_spell_data(spell_data)

        items_with_effect = Items.objects.filter(Q(click_effect=spell_data.id) |
                                                 Q(worn_effect=spell_data.id) |
                                                 Q(proc_effect=spell_data.id))

        try:
            scrolls = Items.objects.filter(scroll_effect=spell_data.id, scroll_type=7)
        except ObjectDoesNotExist:
            scrolls = None
        components = list()
        if spell_data.components1 >= 0:
            components.append((Items.objects.filter(id=spell_data.components1).first(), spell_data.component_counts1))
        if spell_data.components2 >= 0:
            components.append((Items.objects.filter(id=spell_data.components2).first(), spell_data.component_counts2))
        if spell_data.components3 >= 0:
            components.append((Items.objects.filter(id=spell_data.components3).first(), spell_data.component_counts3))
        if spell_data.components4 >= 0:
            components.append((Items.objects.filter(id=spell_data.components4).first(), spell_data.component_counts4))
        result = SpellExpansion.objects.filter(id=spell_id).first()
        expansion = result.expansion if result else None

        spell_patch_history = (
            SpellPatchHistory.objects
            .filter(spell_id=spell_id)
            .select_related('patch')
            .order_by('patch__patch_date')
        )

        return render(request=request,
                      template_name="spells/view_spell.html",
                      context={"spell_data": spell_data,
                               "spell_effects": sp_effects,
                               "expansion": expansion,
                               "scrolls": scrolls,
                               "components": components,
                               "spell_min_duration": spell_min_duration,
                               "spell_min_time": spell_min_time,
                               "spell_max_duration": spell_max_duration,
                               "spell_max_time": spell_max_time,
                               "items_with_effect": items_with_effect,
                               "spell_patch_history": spell_patch_history,
                               },
                      )
