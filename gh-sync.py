import os
import yaml
import github3

with open('.token', 'r') as fp:
    token = fp.readline().strip()

user = os.environ.get('GITHUB_USER', 'Xarthisius')

with open('project.yaml', 'r') as fp:
    data = yaml.load(fp.read())


def get_label_name(label_data, prefix='', color=None):
    labels = []
    for label in label_data:
        if 'subcategories' in label:
            labels += get_label_name(
                label['subcategories'],
                prefix=os.path.join(prefix, label['name']),
                color=label.get('color'))
        if 'meta' not in label or not label['meta']:
            labels.append({
                'name': os.path.join(prefix, label['name']),
                'color': label.get('color', color)
            })
    return labels


new_labels = get_label_name(data['labels'])
new_label_names = {_['name'] for _ in new_labels}

gh = github3.login(user, token)
for repo_name in data['repos']:
    repo = gh.repository(data['org'], repo_name)
    current_labels = list(repo.labels())
    current_label_names = {_.name for _ in current_labels}
    for name in current_label_names & new_label_names:
        label = next(_ for _ in current_labels if _.name == name)
        new_label = next(_ for _ in new_labels if _['name'] == name)
        if label.color != new_label['color']:
            # TODO check description ?
            label.update(new_label['name'], new_label.get('color', 'ffffff'))
    for name in current_label_names - new_label_names:
        label = next(_ for _ in current_labels if _.name == name)
        labeled_issues = list(repo.issues(labels=[label.name]))
        if not labeled_issues:
            label.delete()
        else:
            for issue in labeled_issues:
                print('[%s] Issue #%i is still using label "%s"' %
                      (str(repo), issue.number, label.name))
    for name in new_label_names - current_label_names:
        new_label = next(_ for _ in new_labels if _['name'] == name)
        repo.create_label(new_label['name'], new_label.get('color', 'ffffff'))
