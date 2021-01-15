from orator.migrations import Migration


class RemoveUsersIsDisabled(Migration):

    def up(self):
        """
        Run the migrations.
        """
        with self.schema.table('users') as table:
            table.drop_column('is_disabled')

    def down(self):
        """
        Revert the migrations.
        """
        with self.schema.table('users') as table:
            pass
