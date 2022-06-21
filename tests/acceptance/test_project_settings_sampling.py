from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys

from sentry.api.endpoints.project_details import DynamicSamplingSerializer
from sentry.models import Project
from sentry.testutils import AcceptanceTestCase

FEATURE_NAME = "organizations:filters-and-sampling"


class ProjectSettingsSamplingTest(AcceptanceTestCase):
    def setUp(self):
        super().setUp()
        self.user = self.create_user("foo@example.com")
        self.org = self.create_organization(name="Rowdy Tiger", owner=None)
        self.team = self.create_team(organization=self.org, name="Mariachi Band")
        self.project = self.create_project(organization=self.org, teams=[self.team], name="Bengal")
        self.project.update_option(
            "sentry:dynamic_sampling",
            {
                "next_id": 3,
                "rules": [
                    {
                        "sampleRate": 0.7,
                        "type": "trace",
                        "condition": {
                            "op": "and",
                            "inner": [],
                        },
                        "id": 0,
                    },
                    {
                        "sampleRate": 0.8,
                        "type": "trace",
                        "condition": {
                            "op": "and",
                            "inner": [
                                {
                                    "op": "eq",
                                    "name": "trace.environment",
                                    "value": ["production"],
                                    "options": {"ignoreCase": True},
                                }
                            ],
                        },
                        "id": 1,
                    },
                    {
                        "sampleRate": 0.1,
                        "type": "trace",
                        "condition": {
                            "op": "and",
                            "inner": [
                                {
                                    "op": "glob",
                                    "name": "trace.release",
                                    "value": ["[13].[19]"],
                                }
                            ],
                        },
                        "id": 2,
                    },
                ],
            },
        )
        self.create_member(user=self.user, organization=self.org, role="owner", teams=[self.team])
        self.login_as(self.user)
        self.path = f"/settings/{self.org.slug}/projects/{self.project.slug}/sampling/trace/"

    def wait_until_loaded(self):
        self.browser.get(self.path)
        self.browser.wait_until_not('[data-test-id="loading-indicator"]')

    def test_drag_and_drop_rule_error(self):
        with self.feature(FEATURE_NAME):
            self.wait_until_loaded()

            # Tries to drag rules with conditions below a rule without a condition (flat rule)
            dragHandleSource = self.browser.elements(
                '[data-test-id="sampling-rule"] [aria-roledescription="sortable"]'
            )[1]
            dragHandleTarget = self.browser.elements(
                '[data-test-id="sampling-rule"] [aria-roledescription="sortable"]'
            )[2]

            action = ActionChains(self.browser.driver)
            action.drag_and_drop(dragHandleSource, dragHandleTarget)
            action.perform()

            self.browser.wait_until_test_id("toast-error")

    def test_drag_and_drop_rule_success(self):
        with self.feature(FEATURE_NAME):
            self.wait_until_loaded()

            # Before
            rulesBefore = self.browser.elements('[data-test-id="sampling-rule"]')
            assert "Environment" in rulesBefore[0].text
            assert "Release" in rulesBefore[1].text

            dragHandleSource = self.browser.elements('[aria-roledescription="sortable"]')[1]
            dragHandleTarget = self.browser.elements('[aria-roledescription="sortable"]')[0]

            action = ActionChains(self.browser.driver)
            action.drag_and_drop(dragHandleSource, dragHandleTarget)
            action.perform()

            # After
            rulesAfter = self.browser.elements('[data-test-id="sampling-rule"]')
            assert "Release" in rulesAfter[0].text
            assert "Environment" in rulesAfter[1].text

    def test_tab_switch(self):
        with self.feature(FEATURE_NAME):
            self.wait_until_loaded()

            # Go to individual transactions tab
            self.browser.elements('[role="tab"]')[1].click()

            assert (
                f"/settings/{self.org.slug}/projects/{self.project.slug}/sampling/transaction/"
                in self.browser.driver.current_url
            )

            # There are no transaction rules
            assert (
                len(self.browser.find_elements_by_css_selector('[data-test-id="sampling-rule"]'))
                == 0
            )

            assert self.browser.element_exists('[data-test-id="empty-state"]')

            # Go back to the distributed traces tab
            self.browser.elements('[role="tab"]')[0].click()

            assert (
                f"/settings/{self.org.slug}/projects/{self.project.slug}/sampling/trace/"
                in self.browser.driver.current_url
            )

            # There are transaction rules
            assert self.browser.element_exists('[data-test-id="sampling-rule"]')

            assert (
                len(self.browser.find_elements_by_css_selector('[data-test-id="empty-state"]')) == 0
            )

    def test_add_individual_transaction_rule_with_all_possible_conditions(self):
        with self.feature(FEATURE_NAME):
            self.wait_until_loaded()

            # Go to individual transactions tab
            self.browser.elements('[role="tab"]')[1].click()

            # Open the modal
            self.browser.element('[aria-label="Add Rule"]').click()

            # Open conditions dropdown
            self.browser.element('[aria-label="Add Condition"]').click()

            # Add browser extensions
            self.browser.element('[data-test-id="event.has_bad_browser_extensions"]').click()
            # Add Content Security Policy
            self.browser.element('[data-test-id="event.csp"]').click()
            # Add Device Family
            self.browser.element('[data-test-id="event.contexts.device.family"]').click()
            # Add Device Name
            self.browser.element('[data-test-id="event.contexts.device.name"]').click()
            # Add Environment
            self.browser.element('[data-test-id="event.environment"]').click()
            # Add Error Message
            self.browser.element('[data-test-id="event.error_messages"]').click()
            # Add IP Address
            self.browser.element('[data-test-id="event.client_ip"]').click()
            # Add Legacy Browser
            self.browser.element('[data-test-id="event.legacy_browser"]').click()
            # Add Localhost
            self.browser.element('[data-test-id="event.is_local_ip"]').click()
            # Add OS Name
            self.browser.element('[data-test-id="event.contexts.os.name"]').click()
            # Add OS Version
            self.browser.element('[data-test-id="event.contexts.os.version"]').click()
            # Add Release
            self.browser.element('[data-test-id="event.release"]').click()
            # Add Transaction
            self.browser.element('[data-test-id="event.transaction"]').click()
            # Add User ID
            self.browser.element('[data-test-id="event.user.id"]').click()
            # Add User Segment
            self.browser.element('[data-test-id="event.user.segment"]').click()
            # Add Web Crawlers
            self.browser.element('[data-test-id="event.web_crawlers"]').click()
            # Add Custom Tag
            self.browser.element('[aria-autocomplete="list"]').send_keys("Add cus", Keys.ENTER)

            # Fill in Content Security Policy
            self.browser.element('[placeholder="ex. file://*, example.com (Multiline)"]').send_keys(
                "sentry.io\nwhatever.com"
            )
            # Fill in Device Family
            self.browser.element('[aria-label="Search or add a device family"]').send_keys(
                "Mac", Keys.ENTER, "pixe*", Keys.ENTER
            )
            # Fill in Device Name
            self.browser.element('[aria-label="Search or add a device name"]').send_keys(
                "mac", Keys.ENTER, "ipho*", Keys.ENTER
            )
            # Fill in Environment
            self.browser.element('[aria-label="Search or add an environment"]').send_keys(
                "prod", Keys.ENTER, "production", Keys.ENTER
            )
            # Fill in Error Message
            self.browser.element('[placeholder="ex. TypeError* (Multiline)"]').send_keys(
                "TypeError*\nSomethingElse"
            )
            # Fill in IP Address
            self.browser.element(
                '[placeholder="ex. 127.0.0.1 or 10.0.0.0/8 (Multiline)"]'
            ).send_keys("10.0.0.0/8\n127.0.0.1")
            # Enable All Browsers
            self.browser.elements('[data-test-id="switch"]')[0].click()
            # Fill in OS Name
            self.browser.element('[aria-label="Search or add an os name"]').send_keys(
                "Mac OS X", Keys.ENTER, "Windo*", Keys.ENTER
            )
            # Fill in OS Version
            self.browser.element('[placeholder="ex. 11, 9* (Multiline)"]').send_keys("11")
            # Fill in Release
            self.browser.element('[aria-label="Search or add a release"]').send_keys(
                "frontend@22*", Keys.ENTER
            )
            # Fill in Transaction
            self.browser.element('[aria-label="Search or add a transaction"]').send_keys(
                "/organizations/:orgId/alerts/:projectId/wizard/",
                Keys.ENTER,
                "/organizations/:orgId/alerts/rules/",
                Keys.ENTER,
            )
            # Fill in User ID
            self.browser.element('[placeholder="ex. 4711 (Multiline)"]').send_keys("4711\n1")
            # Fill in User Segment
            self.browser.element('[placeholder="ex. paid, common (Multiline)"]').send_keys(
                "paid\ncommon"
            )
            # Fill in Custom Tag
            self.browser.element('[aria-label="Search or add a tag"]').send_keys(
                "DOMException.code", Keys.ENTER
            )
            self.browser.element('[aria-label="Search or add tag values"]').send_keys(
                "20", Keys.ENTER
            )
            # Fill in sample rate
            self.browser.element('[placeholder="%"]').send_keys("50")

            # Save rule
            self.browser.element('[aria-label="Save Rule"]').click()

            # Wait the success message to show up
            self.browser.wait_until('[data-test-id="toast-success"]')

            # Take a screenshot
            self.browser.snapshot("sampling settings rule with all possible conditions")

            # Validate the payload
            project = Project.objects.get(pk=self.project.id)
            saved_sampling_setting = project.get_option("sentry:dynamic_sampling")
            serializer = DynamicSamplingSerializer(data=saved_sampling_setting)
            assert serializer.is_valid()
            assert saved_sampling_setting == serializer.validated_data
