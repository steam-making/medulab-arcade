import os, sys
sys.path.insert(0, r'E:\making_project\medulab_arcade')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'medulab_arcade.settings')
import django; django.setup()
from courses.models import RoadmapTrack, RoadmapNode

track = RoadmapTrack.objects.get(id=7)  # 타자 트랙

node, created = RoadmapNode.objects.get_or_create(
    roadmap_track=track,
    roadmap_grade='kids_5_7',
    defaults={'title': '전체자리익히기', 'subtitle': '키보드 자리 익히기 / 목표 100타'}
)
if not created:
    node.title = '전체자리익히기'
    node.subtitle = '키보드 자리 익히기 / 목표 100타'
    node.save(update_fields=['title', 'subtitle'])

print(f"{'Created' if created else 'Updated'} [kids_5_7]: {node.title} / {node.subtitle}")

print("\n최종 타자 트랙:")
for n in RoadmapNode.objects.filter(roadmap_track=track).order_by('roadmap_grade'):
    print(f"  [{n.roadmap_grade}] {n.title} / {n.subtitle}")
