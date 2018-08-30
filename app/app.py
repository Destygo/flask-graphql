from flask import Flask
from custom_flask_graphql import GraphQLView
from schema import schema
from json_cleaning import JSonCleaning


def create_app(path='/graphql', **kwargs):
    backend = None
    app = Flask(__name__, static_url_path='/static')
    app.debug = True
    app.add_url_rule(path, view_func=GraphQLView.as_view('graphql', schema=schema, backend=backend, context=JSonCleaning.key_map, **kwargs))
    print('Add URL rule: succeeded')
    return app


if __name__ == '__main__':
    app = create_app(graphiql=True)
    app.run()
