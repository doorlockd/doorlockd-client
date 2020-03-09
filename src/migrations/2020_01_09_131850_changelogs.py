from orator.migrations import Migration


class Changelogs(Migration):

	def up(self):
		"""
		Run the migrations.
		"""
		with self.schema.create('changelogs') as table:
			table.increments('id')
			table.morphs('changelogger')
			
			table.string('action')
			table.json('diff').default('[]')
			
			table.datetime('prev').nullable()
			table.datetime('now').nullable()
			
			table.integer('user_id').unisgned().nullable()
			table.foreign('user_id').references('id').on('users')
		
		

	def down(self):
		"""
		Revert the migrations.
		"""
		self.schema.drop('changelogs')
		
