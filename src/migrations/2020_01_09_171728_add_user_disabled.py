from orator.migrations import Migration


class AddUserDisabled(Migration):

	def up(self):
		"""
		Run the migrations.
		"""
		with self.schema.table('users') as table:
			table.boolean('is_disabled').default(False)
			

	def down(self):
		"""
		Revert the migrations.
		"""
		with self.schema.table('users') as table:
			table.drop_column('is_disabled')
		
