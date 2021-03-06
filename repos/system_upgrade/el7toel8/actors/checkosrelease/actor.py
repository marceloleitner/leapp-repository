import os

from leapp.actors import Actor
from leapp.models import CheckResult, OSReleaseFacts, Inhibitor
from leapp.tags import ChecksPhaseTag, IPUWorkflowTag


class CheckOSRelease(Actor):
    """
    Check if a supported release version of system's OS is in use. If not, inhibit upgrade process.

    Based on OS release collected facts, this actor will compare current release with supported
    versions. If a problem is found an inhibition message will be generated. This check can be
    skipped by using LEAPP_SKIP_CHECK_OS_RELEASE environment variable.
    """

    name = 'check_os_release'
    consumes = (OSReleaseFacts,)
    produces = (CheckResult, Inhibitor)
    tags = (ChecksPhaseTag, IPUWorkflowTag,)

    def process(self):
        skip_check = os.getenv('LEAPP_SKIP_CHECK_OS_RELEASE')
        if skip_check:
            self.produce(CheckResult(
                severity='Warning',
                result='Not Applicable',
                summary='Skipped OS release check',
                details='OS release check skipped via LEAPP_SKIP_CHECK_OS_RELEASE env var',
                solutions=None
            ))
            return

        min_supported_version = {
            'rhel': '7.6'
        }

        for facts in self.consume(OSReleaseFacts):
            if facts.id not in min_supported_version.keys():
                self.produce(Inhibitor(
                    summary='Unsupported OS id',
                    details='Supported OS ids for upgrade process: ' + ','.join(min_supported_version.keys()),
                    solutions=None
                ))
                return

            min_version = [int(x) for x in min_supported_version[facts.id].split('.')]
            os_version = [int(x) for x in facts.version_id.split('.')]

            for current, minimal in zip(os_version, min_version):
                if current > minimal:
                    break

                if current < minimal:
                    self.produce(Inhibitor(
                        summary='Unsupported OS version',
                        details='Minimal supported OS version for upgrade process: ' + min_supported_version[facts.id],
                        solutions=None
                    ))
                    return
