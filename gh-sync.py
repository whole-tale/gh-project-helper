import os
import yaml
import github3


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


def process_labels(data, gh):
    """
    Handles creating labels for an organization.

    :param data: The config file contents
    :param gh: The GitHub user
    """
    new_labels = get_label_name(data['labels'])
    new_label_names = {_['name'] for _ in new_labels}

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


def get_milestone_name(milestone_data, prefix='', color=None):
    milestones = []
    for milestone in milestone_data:
        milestones.append({
            'name': os.path.join(prefix, str(milestone['name']))
        })
    return milestones


def process_milestones(data, gh):
    """
    Creates milestones for the organization.
    :param data: The config file contents
    :param gh: The GitHub user
    """
    new_milestones = get_milestone_name(data['milestones'])
    new_milestone_names = [_['name'] for _ in new_milestones]
    new_milestone_names.sort()

    for repo_name in data['repos']:
        repo = gh.repository(data['org'], repo_name)
        current_milestones = list(repo.milestones())
        current_milestone_names = {_.title for _ in current_milestones}

        for name in current_milestone_names - set(new_milestone_names):
            milestone = next(_ for _ in current_milestones if _.name == name)
            milestoned_issues = list(repo.issues(milestone=[milestone.name]))
            if not milestoned_issues:
                milestone.delete()
            else:
                for issue in milestoned_issues:
                    print('[%s] Issue #%i is still using milestone "%s"' %
                        (str(repo), issue.number, milestone.name))
        for name in set(new_milestone_names) - current_milestone_names:
            new_milestone = next(_ for _ in new_milestones if _['name'] == name)
            repo.create_milestone(new_milestone['name'])


if __name__ == "__main__":
    user = os.environ.get('GITHUB_USER', 'Xarthisius')

    with open('.token', 'r') as fp:
        token = fp.readline().strip()

    gh = github3.login(user, token)

    with open('project.yaml', 'r') as fp:
        data = yaml.load(fp.read())

    process_labels(data, gh)
    process_milestones(data, gh)
