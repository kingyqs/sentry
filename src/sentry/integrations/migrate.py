from __future__ import absolute_import

from sentry.models import Repository
from sentry.plugins import plugins
from sentry.utils.cache import memoize


DISABLEABLE_PLUGINS = (
    'vsts',
    'bitbucket',
    'github',
    'example',  # Tests
)


class PluginMigrator(object):
    def __init__(self, integration, organization):
        self.integration = integration
        self.organization = organization

    def call(self):
        for project in self.projects:
            for plugin in plugins.for_project(project):
                if plugin.slug not in DISABLEABLE_PLUGINS:
                    continue

                if self.all_repos_migrated(plugin.slug):
                    # Since repos are Org-level, if they're all migrated, we
                    # can disable the Plugin for all Projects. There'd be no
                    # Repos left, associated with the Plugin.
                    self.disable_for_all_projects(plugin)

    def all_repos_migrated(self, provider):
        provider = 'visualstudio' if provider == 'vsts' else provider

        return all(
            r.integration_id is not None
            for r in self.repos_for_provider(provider)
        )

    def disable_for_all_projects(self, plugin):
        for project in self.projects:
            try:
                plugin.disable(project=project)
            except NotImplementedError:
                pass

    def repos_for_provider(self, provider):
        return filter(lambda r: r.provider == provider, self.repositories)

    @property
    def repositories(self):
        return Repository.objects.filter(
            organization_id=self.organization.id,
        )

    @memoize
    def projects(self):
        return list(self.organization.project_set.all())

    @property
    def plugins(self):
        return [
            plugins.configurable_for_project(project)
            for project in self.projects
        ]
