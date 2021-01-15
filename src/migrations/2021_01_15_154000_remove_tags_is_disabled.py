from orator.migrations import Migration


class RemoveTagsIsDisabled(Migration):

    def up(self):
        """
        Run the migrations.
        """
        with self.schema.table('tags') as table:
            table.drop_column('is_disabled')

    def down(self):
        """
        Revert the migrations.
        """
        with self.schema.table('tags') as table:
            pass
