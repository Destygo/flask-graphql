import json
import jmespath
from ast import literal_eval
import re


class MockGetBuilder:

    @classmethod
    def _generate_closure(cls, size):
        if size <= 1:
            return ["", "'", "': 'TOKEN'", "\""]
        else:
            res = []
            for e in cls._generate_closure(size - 1):
                res.append(e)
                res.append(e + "]")
                res.append(e + "}")
            return res

    @classmethod
    def _estimate_imbalance_size(cls, s):
        res = (len(re.findall("{", s)) - len(re.findall("}", s)))
        res += (len(re.findall("\[", s)) - len(re.findall("\]", s)))
        res += int(len(re.findall("'", s)) % 2 == 0)
        res += int(len(re.findall("\"", s)) % 2 == 0)
        return res

    @classmethod
    def _load_hybrid_json(cls, hybrid):
        if isinstance(hybrid, dict):
            res = {}
            for e in hybrid:
                res[e] = cls._load_hybrid_json(hybrid[e])
            return res
        elif isinstance(hybrid, list):
            res = []
            for e in hybrid:
                res.append(cls._load_hybrid_json(e))
            return res
        else:
            try:
                j = literal_eval(hybrid)
                return j
            except Exception:
                if "'" in hybrid or '"' in hybrid or "{" in hybrid or "[" in hybrid:
                    candidates = cls._generate_closure(cls._estimate_imbalance_size(hybrid)) + cls._generate_closure(10)
                    candidates.sort(key=len, reverse=True)
                    for closure in candidates:
                        try:
                            j = literal_eval(hybrid + closure)
                            return j
                        except Exception:
                            pass
                print("ERROR", type(hybrid))
                # print(hybrid)
                return hybrid

    @classmethod
    def normalize_api_trace_json(cls, input_file_name, output_file_name):
        with open(input_file_name, 'r') as file:
            result = []
            for call in jmespath.search('values(@)[?"0".url].["0", "1", "2", "3", "4", "5", "6", "7", "8", "9"][]\
                                        .{url: url, query_result: query_result}', json.load(file)):
                result.append({
                    'url': call['url'],
                    'query_result': cls._load_hybrid_json(call['query_result'])
                })
        with open(output_file_name, 'w') as file:
            json.dump(result, file, indent=4, ensure_ascii=False, sort_keys=True)

    @staticmethod
    def _mock_get(file_name, url, params={}, headers={}):
        class MockResponse:
            def __init__(self, json_data, status_code):
                self.json_data = json_data
                self.status_code = status_code

            def json(self):
                return self.json_data
        with open(file_name, 'r') as file:
            query_result = jmespath.search("[?url=='{}'] | [0].query_result".format(url), json.load(file))
        if query_result:
            return MockResponse(query_result, 200)
        else:
            return MockResponse(None, 404)

    @classmethod
    def build_mock_get_from_file(cls, file_name):
        with open(file_name, 'r') as file:
            fun = lambda x, y={}, z={}: cls._mock_get(file_name, x, y, z)
        return fun
