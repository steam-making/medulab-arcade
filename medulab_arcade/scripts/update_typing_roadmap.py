import os, sys
sys.path.insert(0, r'E:\making_project\medulab_arcade')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'medulab_arcade.settings')
import django; django.setup()
from courses.models import RoadmapTrack, RoadmapNode

track = RoadmapTrack.objects.get(id=7)  # 타자 트랙

updates = {
    'elem_1_2': '단어 200타 / 짧은글 150타',
    'elem_3_4': '단어 250타 / 짧은글 200타 / 긴글 150타',
    'elem_5_6': '단어 300타 / 짧은글 300타 / 긴글 250타',
}

for grade, subtitle in updates.items():
    node = RoadmapNode.objects.filter(roadmap_track=track, roadmap_grade=grade).first()
    if node:
        node.subtitle = subtitle
        node.save(update_fields=['subtitle'])
        print(f"Updated [{grade}]: {subtitle}")

# 중고등 노드 추가 (없으면)
node_mh, created = RoadmapNode.objects.get_or_create(
    roadmap_track=track,
    roadmap_grade='mid_high',
    defaults={'title': '목표타자', 'subtitle': '단어 400타 / 짧은글 400타 / 긴글 350타'}
)
if not created:
    node_mh.subtitle = '단어 400타 / 짧은글 400타 / 긴글 350타'
    node_mh.save(update_fields=['subtitle'])
print(f"{'Created' if created else 'Updated'} [mid_high]: {node_mh.subtitle}")

print("\n최종 확인:")
for node in RoadmapNode.objects.filter(roadmap_track=track).order_by('roadmap_grade'):
    print(f"  [{node.roadmap_grade}] {node.title} / {node.subtitle}")
