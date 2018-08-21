import genson
import graphene
from graphene.types.objecttype import ObjectTypeOptions, BaseOptions
import json
import requests
import sys
from unittest import mock

from json_cleaning import JSonCleaning
from mock_get_builder import MockGetBuilder


# mock_get = MockGetBuilder.build_mock_get_from_file('api_trace_normalized.json')


class SchemaBuilder:

    TYPE_TRANSLATION = {
        "object": graphene.ObjectType,
        "string": graphene.String,
        "array": graphene.List,
        "number": graphene.Float,
        "integer": graphene.Int,
        "boolean": graphene.Boolean
    }
    SCALARS = ["string", "number", "integer", "boolean"]

    def __init__(self):
        self.object_types = {}

    @staticmethod
    # @mock.patch('requests.get', mock_get)
    def urls_to_json_schema(urls):
        builder = genson.SchemaBuilder()
        builder.add_schema({"type": "object", "properties": {}})
        for url in urls:
            response = requests.get(url)
            if response.status_code == 200:
                builder.add_object(JSonCleaning.clean_keys(response.json()))
            else:
                print("Error {} while fetching url {}".format(response.status_code, url))
        builder.to_schema()
        schema = builder.to_json(indent=4)
        return json.loads(schema)

    def json_schema_to_graphene_object_type(self, name, schema):
        """:return : type, object"""
        if schema['type'] in SchemaBuilder.SCALARS:
            return 'scalar', SchemaBuilder.TYPE_TRANSLATION[schema['type']]
        elif schema['type'] == 'array':
            if 'items' in schema:
                _, T = self.json_schema_to_graphene_object_type(name, schema['items'])
                return 'array', T
            else:
                return 'array', graphene.String
        elif schema['type'] == 'object':
            if name in self.object_types:
                return 'object', self.object_types[name]
            options = ObjectTypeOptions(BaseOptions)
            options.fields = {'raw': graphene.Field(graphene.JSONString)}
            for field in schema['properties']:
                t, T = self.json_schema_to_graphene_object_type(field, schema['properties'][field])
                if t == 'array':
                    resolver = lambda self, info, field=field, T=T: [T(raw=sub_raw) for sub_raw in self.raw[field]]
                    options.fields[field] = graphene.Field(graphene.List(T), resolver=resolver)
                elif t == 'object':
                    resolver = lambda self, info, field=field, T=T: T(raw=self.raw[field])
                    options.fields[field] = graphene.Field(T, resolver=resolver)
                else:
                    resolver = lambda self, info, field=field: self.raw[field]
                    options.fields[field] = graphene.Field(T, resolver=resolver)
            object_type = graphene.ObjectType.create_type(class_name=name, _meta=options)
            self.object_types[name] = object_type
            return 'object', object_type
        else:
            print("UNKNOWN TYPE", schema['type'])

    def urls_to_graphene_object_type(self, name, urls):
        _, T = self.json_schema_to_graphene_object_type(name, self.urls_to_json_schema(urls))
        return T


# @mock.patch('requests.get', mock_get)
def build_query(urls, print_example=False):
    T = SchemaBuilder().urls_to_graphene_object_type('test', urls)
    if print_example:
        print(json.dumps(requests.get(urls[0]).json(), indent=4, ensure_ascii=False))

    return T

# Global variables

urls = [
    # "https://cms-api.lyonaeroports.com/api/v1/ftd01desk/fr/list/destination.json?"
    "http://apixha.ixxi.net/APIX?keyapp=lcvghKtoRkpmDszTzghE&cmd=getItinerary&endPointLat=48.845084&endPointLon=2.373209&startPointLat=48.846454&startPointLon=2.418598&leaveTime=&engine=ratp&apixFormat=json&prefModes=all&approachModes=walk&withEcoComparator=true&startFrom=true&prefJourney=rvbFaster&withText=true&withTrafficEvents=false"
    # "https://ratp-prod3.onyourmap.com/oym?f=gac&charset=UTF-8&profile=ratp_bot&comp=gare de lyon&mx=12&_=1500306489918"
]
T = build_query(urls)
raw = JSonCleaning.clean_keys(requests.get(urls[0]).json())


class Query(graphene.ObjectType):
    global T, raw
    a = graphene.Field(T)
    b = graphene.Field(graphene.Int)


    def resolve_a(self, info):
        return T(raw=raw)

    def resolve_b(self, info):
        return 1


schema = graphene.Schema(query=Query, auto_camelcase=False)
