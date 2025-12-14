import random
from ..models import Ad, AdWatch
from django.conf import settings


def get_ads_for_report(user, report):
    watched_ad_ids = AdWatch.objects.filter(
        user=user,
        report=report
    ).values_list('ad_id', flat=True)

    available_ads = Ad.objects.filter(
        is_active=True
    ).exclude(id__in=watched_ad_ids)

    ads = list(available_ads)
    random.shuffle(ads)

    return ads[:settings.ADS_REQUIRED_PER_REPORT]
