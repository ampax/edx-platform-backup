"""
Acceptance tests for Studio's Setting pages
"""

from nose.plugins.attrib import attr

from base_studio_test import StudioCourseTest

from ...pages.studio.settings_advanced import AdvancedSettingsPage
from ...pages.studio.settings_group_configurations import GroupConfigurationsPage


@attr('shard_1')
class ContentGroupConfigurationTest(StudioCourseTest):
    """
    Tests for content groups in the Group Configurations Page.
    There are tests for the experiment groups in test_studio_split_test.
    """
    def setUp(self):
        super(ContentGroupConfigurationTest, self).setUp()
        self.group_configurations_page = GroupConfigurationsPage(
            self.browser,
            self.course_info['org'],
            self.course_info['number'],
            self.course_info['run']
        )

    def create_and_verify_content_group(self, name, existing_groups):
        """
        Creates a new content group and verifies that it was properly created.
        """
        self.assertEqual(existing_groups, len(self.group_configurations_page.content_groups))
        if existing_groups == 0:
            self.group_configurations_page.create_first_content_group()
        else:
            self.group_configurations_page.add_content_group()
        config = self.group_configurations_page.content_groups[existing_groups]
        config.name = name
        # Save the content group
        self.assertEqual(config.get_text('.action-primary'), "Create")
        self.assertTrue(config.delete_button_is_absent)
        config.save()
        self.assertIn(name, config.name)
        return config

    def test_no_content_groups_by_default(self):
        """
        Scenario: Ensure that message telling me to create a new content group is
            shown when no content groups exist.
        Given I have a course without content groups
        When I go to the Group Configuration page in Studio
        Then I see "You have not created any content groups yet." message
        """
        self.group_configurations_page.visit()
        self.assertTrue(self.group_configurations_page.no_content_groups_message_is_present)
        self.assertIn(
            "You have not created any content groups yet.",
            self.group_configurations_page.no_content_groups_message_text
        )

    def test_can_create_and_edit_content_groups(self):
        """
        Scenario: Ensure that the content groups can be created and edited correctly.
        Given I have a course without content groups
        When I click button 'Add your first Content Group'
        And I set new the name and click the button 'Create'
        Then I see the new content is added and has correct data
        And I click 'New Content Group' button
        And I set the name and click the button 'Create'
        Then I see the second content group is added and has correct data
        When I edit the second content group
        And I change the name and click the button 'Save'
        Then I see the second content group is saved successfully and has the new name
        """
        self.group_configurations_page.visit()
        self.create_and_verify_content_group("New Content Group", 0)
        second_config = self.create_and_verify_content_group("Second Content Group", 1)

        # Edit the second content group
        second_config.edit()
        second_config.name = "Updated Second Content Group"
        self.assertEqual(second_config.get_text('.action-primary'), "Save")
        second_config.save()

        self.assertIn("Updated Second Content Group", second_config.name)

    def test_cannot_delete_content_group(self):
        """
        Scenario: Delete is not currently supported for content groups.
        Given I have a course without content groups
        When I create a content group
        Then there is no delete button
        """
        self.group_configurations_page.visit()
        config = self.create_and_verify_content_group("New Content Group", 0)
        self.assertTrue(config.delete_button_is_absent)

    def test_must_supply_name(self):
        """
        Scenario: Ensure that validation of the content group works correctly.
        Given I have a course without content groups
        And I create new content group without specifying a name click the button 'Create'
        Then I see error message "Content Group name is required."
        When I set a name and click the button 'Create'
        Then I see the content group is saved successfully
        """
        self.group_configurations_page.visit()
        self.group_configurations_page.create_first_content_group()
        config = self.group_configurations_page.content_groups[0]
        config.save()
        self.assertEqual(config.mode, 'edit')
        self.assertEqual("Group name is required", config.validation_message)
        config.name = "Content Group Name"
        config.save()
        self.assertIn("Content Group Name", config.name)

    def test_can_cancel_creation_of_content_group(self):
        """
        Scenario: Ensure that creation of a content group can be canceled correctly.
        Given I have a course without content groups
        When I click button 'Add your first Content Group'
        And I set new the name and click the button 'Cancel'
        Then I see that there is no content groups in the course
        """
        self.group_configurations_page.visit()
        self.group_configurations_page.create_first_content_group()
        config = self.group_configurations_page.content_groups[0]
        config.name = "Content Group"
        config.cancel()
        self.assertEqual(0, len(self.group_configurations_page.content_groups))


@attr('shard_1')
class AdvancedSettingsValidationTest(StudioCourseTest):
    """
    Tests for validation feature in Studio's advanced settings tab
    """
    def setUp(self):
        super(AdvancedSettingsValidationTest, self).setUp()
        self.advanced_settings = AdvancedSettingsPage(
            self.browser,
            self.course_info['org'],
            self.course_info['number'],
            self.course_info['run']
        )

        self.type_fields = ['Course Display Name', 'Advanced Module List', 'Discussion Topic Mapping',
                            'Maximum Attempts', 'Course Announcement Date']

        # Before every test, make sure to visit the page first
        self.advanced_settings.visit()
        self.assertTrue(self.advanced_settings.is_browser_on_page())

    def test_modal_shows_one_validation_error(self):
        """
        Test that advanced settings don't save if there's a single wrong input,
        and that it shows the correct error message in the modal.
        """

        # Feed an integer value for String field.
        # .set method saves automatically after setting a value
        course_display_name = self.advanced_settings.get('Course Display Name')
        self.advanced_settings.set('Course Display Name', 1)
        self.advanced_settings.wait_for_modal_load()

        # Test Modal
        self.check_modal_shows_correct_contents(['Course Display Name'])
        self.advanced_settings.refresh_and_wait_for_load()

        self.assertEquals(
            self.advanced_settings.get('Course Display Name'),
            course_display_name,
            'Wrong input for Course Display Name must not change its value'
        )

    def test_modal_shows_multiple_validation_errors(self):
        """
        Test that advanced settings don't save with multiple wrong inputs
        """

        # Save original values and feed wrong inputs
        original_values_map = self.get_settings_fields_of_each_type()
        self.set_wrong_inputs_to_fields()
        self.advanced_settings.wait_for_modal_load()

        # Test Modal
        self.check_modal_shows_correct_contents(self.type_fields)
        self.advanced_settings.refresh_and_wait_for_load()

        for key, val in original_values_map.iteritems():
            self.assertEquals(
                self.advanced_settings.get(key),
                val,
                'Wrong input for Advanced Settings Fields must not change its value'
            )

    def test_undo_changes(self):
        """
        Test that undo changes button in the modal resets all settings changes
        """

        # Save original values and feed wrong inputs
        original_values_map = self.get_settings_fields_of_each_type()
        self.set_wrong_inputs_to_fields()

        # Let modal popup
        self.advanced_settings.wait_for_modal_load()

        # Press Undo Changes button
        self.advanced_settings.undo_changes_via_modal()

        # Check that changes are undone
        for key, val in original_values_map.iteritems():
            self.assertEquals(
                self.advanced_settings.get(key),
                val,
                'Undoing Should revert back to original value'
            )

    def test_manual_change(self):
        """
        Test that manual changes button in the modal keeps settings unchanged
        """
        inputs = {"Course Display Name": 1,
                  "Advanced Module List": 1,
                  "Discussion Topic Mapping": 1,
                  "Maximum Attempts": '"string"',
                  "Course Announcement Date": '"string"',
                  }

        self.set_wrong_inputs_to_fields()
        self.advanced_settings.wait_for_modal_load()
        self.advanced_settings.trigger_manual_changes()

        # Check that the validation modal went away.
        self.assertFalse(self.advanced_settings.is_validation_modal_present())

        # Iterate through the wrong values and make sure they're still displayed
        for key, val in inputs.iteritems():
            print self.advanced_settings.get(key)
            print val
            self.assertEquals(
                str(self.advanced_settings.get(key)),
                str(val),
                'manual change should keep: ' + str(val) + ', but is: ' + str(self.advanced_settings.get(key))
            )

    def check_modal_shows_correct_contents(self, wrong_settings_list):
        """
        Helper function that checks if the validation modal contains correct
        error messages.
        """
        # Check presence of modal
        self.assertTrue(self.advanced_settings.is_validation_modal_present())

        # List of wrong settings item & what is presented in the modal should be the same
        error_item_names = self.advanced_settings.get_error_item_names()
        self.assertEqual(set(wrong_settings_list), set(error_item_names))

        error_item_messages = self.advanced_settings.get_error_item_messages()
        self.assertEqual(len(error_item_names), len(error_item_messages))

    def get_settings_fields_of_each_type(self):
        """
        Get one of each field type:
           - String: Course Display Name
           - List: Advanced Module List
           - Dict: Discussion Topic Mapping
           - Integer: Maximum Attempts
           - Date: Course Announcement Date
        """
        return {
            "Course Display Name": self.advanced_settings.get('Course Display Name'),
            "Advanced Module List": self.advanced_settings.get('Advanced Module List'),
            "Discussion Topic Mapping": self.advanced_settings.get('Discussion Topic Mapping'),
            "Maximum Attempts": self.advanced_settings.get('Maximum Attempts'),
            "Course Announcement Date": self.advanced_settings.get('Course Announcement Date'),
        }

    def set_wrong_inputs_to_fields(self):
        """
        Set wrong values for the chosen fields
        """
        self.advanced_settings.set_values(
            {
                "Course Display Name": 1,
                "Advanced Module List": 1,
                "Discussion Topic Mapping": 1,
                "Maximum Attempts": '"string"',
                "Course Announcement Date": '"string"',
            }
        )
