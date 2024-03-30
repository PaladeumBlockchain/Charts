from .models import Block
from pony import orm

class BlockService(object):
    @classmethod
    def latest_block(cls):
        return Block.select().order_by(
            orm.desc(Block.height)
        ).first()

    @classmethod
    def create(cls, blockhash, height, created):
        return Block(**{
            "blockhash": blockhash,
            "created": created,
            "height": height
       })

    @classmethod
    def get_by_height(cls, height):
        return Block.get(height=height)

    @classmethod
    def get_by_hash(cls, bhash):
        return Block.get(blockhash=bhash)

    @classmethod
    def blocks(cls):
        return Block.select().order_by(
            orm.desc(Block.height)
        )
