from radgraph import RadGraph
from radgraph import get_radgraph_processed_annotations


class NERModel():

    def __init__(self, model_type="modern-radgraph-xl"):
        self.model_rad = RadGraph(model_type=model_type)

    def annotate_report(self, report: str):
        return self.model_rad([report])

    def process_annotation(self, annotations: dict):
        return get_radgraph_processed_annotations(annotations)

    def process_data(self, report: str):
        processed_annotations = self.process_annotation(self.annotate_report(report))
        res = list()
        for annotation in processed_annotations["processed_annotations"]:
            tmp = dict()
            if annotation.get("tags", None) is not None:
                tmp['observation'] = annotation.get("observation", "")
                tmp['located_at'] = annotation.get("located_at", "unknown")
                tmp['tags'] = annotation.get("tags", ['unknown'])[0]
                res.append(tmp)
        return res, processed_annotations

