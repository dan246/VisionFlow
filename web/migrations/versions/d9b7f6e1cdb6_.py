"""empty message

Revision ID: d9b7f6e1cdb6
Revises: af0b14c2e267
Create Date: 2024-10-02 08:10:47.052762

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd9b7f6e1cdb6'
down_revision = 'af0b14c2e267'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('camera', schema=None) as batch_op:
        batch_op.add_column(sa.Column('recognition', sa.String(length=255), nullable=True))
        batch_op.create_foreign_key(None, 'user', ['user_id'], ['id'])
        batch_op.drop_column('location')

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('camera', schema=None) as batch_op:
        batch_op.add_column(sa.Column('location', sa.VARCHAR(length=255), autoincrement=False, nullable=True))
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.drop_column('recognition')

    # ### end Alembic commands ###
