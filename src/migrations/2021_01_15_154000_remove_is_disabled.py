from orator.migrations import Migration


class RemoveIsDisabled(Migration):

    def up(self):
        """
        Run the migrations.
        """
        with self.schema.table('users') as table:
            table.drop_column('is_disabled')

        with self.schema.table('tags') as table:
            table.drop_column('is_disabled')

    def down(self):
        """
        Revert the migrations.
        """
        with self.schema.table('tags') as table:
            pass

        with self.schema.table('users') as table:
            pass
