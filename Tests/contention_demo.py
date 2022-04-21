import os
import re

from git import Repo, HEAD
from networkx import MultiDiGraph

test = {
    ('p a', 'works on', 'm 1'),
    ('p a', 'works on', 'm 2'),
    ('p b', 'works on', 'm 1'),
    ('p b', 'works on', 'm 2'),
    ('p c', 'works on', 'm 1'),
    ('p c', 'works on', 'm 1'),
    ('m 1', 'reads from', 't 1'),
    ('m 2', 'reads from', 't 1'),
    ('m 2', 'writes to', 't 1'),
}

g = MultiDiGraph()
for consumer, rel, resource in test:
    g.add_edge(consumer, resource, relation=rel)

repo_path = '/Users/christopherwheeler/dev/Kajabi/kajabi-products'
repo = Repo(repo_path)
models_path = os.path.join(repo_path, 'app/models')
controllers_path = os.path.join(repo_path, 'app/controllers')
model_class_pattern = re.compile(r'class (\w+)\s?<\s?ActiveRecord::Base')
controller_class_pattern = re.compile(r'class (.*)')


def test_thing():
    relationships = set()

    # models
    models = set()
    for root, subdirs, files in os.walk(models_path):
        for f in files:
            current_class = None
            path = os.path.join(root, f)
            blame = repo.blame('HEAD', path)
            committers = set()
            for commit, lines in blame:
                email = commit.author.email
                committers.add(email)
                match = model_class_pattern.match(lines[0])
                if match:
                    current_class = match.group(1)
                    models.add(current_class)
            if current_class:
                rels = {(x, 'works on', current_class) for x in committers}
                relationships |= rels

    # controllers
    for root, subdirs, files in os.walk(controllers_path):
        for f in files:
            current_class = None
            path = os.path.join(root, f)
            blame = repo.blame('HEAD', path)
            committers = set()
            for commit, lines in blame:
                email = commit.author.email
                committers.add(email)
                match = controller_class_pattern.match(lines[0])
                if match:
                    current_class = match.group(1)
                    models.add(current_class)

                line_parts = line[0].split(' ,():')

            if current_class:
                rels = {(x, 'works on', current_class) for x in committers}
                relationships |= rels
                line_parts = set(re.split(r'\s|,|\.|\(|\)', line[0]))
                intersection = line_parts & models
                for model in intersection:
                    tmp = (current_class, 'uses', model)
                    relationships.add(tmp)


    import json
    with open('data.json', 'w') as f:
        json.dump(list(relationships), f)
