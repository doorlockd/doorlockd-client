from orator.migrations import Migration


class ChangeUserIsDisabledToIsEnabled(Migration):

    def up(self):
        """
        Run the migrations.
        """
        with self.schema.table('user') as table:
            # run ('UPDATE users SET is_disabled = NOT is_disabled')
            schema.rename('is_disabled', 'is_enabled')

    def down(self):
        """
        Revert the migrations.
        """
        with self.schema.table('user') as table:
            schema.rename('is_enabled', 'is_disabled')
            
