import json
from datetime import datetime, timedelta
from dataclasses import dataclass


@dataclass
class BlockBuildingTime:
    fcu_time: timedelta
    get_time: timedelta
    new_time: timedelta
    fcu_no_attr_time: timedelta
    total_time: timedelta
    block_number: int
    block_hash: str
    gas_used: int

    def json(self):
        return json.dumps({
            'fcu_time': self.fcu_time.total_seconds(),
            'get_time': self.get_time.total_seconds(),
            'new_time': self.new_time.total_seconds(),
            'fcu_no_attr_time': self.fcu_no_attr_time.total_seconds(),
            'total_time': self.total_time.total_seconds(),
            'block_number': self.block_number,
            'block_hash': self.block_hash,
            'gas_used': self.gas_used,
        })


class LogProcessor:
    fcu_start_ts = None
    get_start_ts = None
    new_start_ts = None
    fcu_no_attr_start_ts = None
    fcu_time = None
    get_time = None
    new_time = None
    fcu_no_attr_time = None
    total_time = None
    block_ts = None
    block_number = None
    block_hash = None
    payload_id = None
    result_file = None
    gas_used_dict = None

    def __init__(self):
        self.result_file = open('./block_building_time.json', 'w')
        with open('./base_gas_used.json', 'r') as f:
            self.gas_used_dict = json.load(f)

    def reset(self):
        self.fcu_start_ts = None
        self.get_start_ts = None
        self.new_start_ts = None
        self.fcu_no_attr_start_ts = None
        self.fcu_time = None
        self.get_time = None
        self.new_time = None
        self.fcu_no_attr_time = None
        self.total_time = None
        self.block_ts = None
        self.block_number = None
        self.block_hash = None
        self.payload_id = None

    def before_fcu(self, log, ts):
        if log['attr'] is None:
            if self.fcu_start_ts is None:
                return
            if self.fcu_no_attr_start_ts is not None:
                raise Exception("fcu_no_attr_start_ts is not None")
            if log['state']['headBlockHash'] != self.block_hash:
                raise Exception('block hash mismatch')
            self.fcu_no_attr_start_ts = ts
        else:
            if self.fcu_start_ts is not None:
                print("fcu_start_ts is not None")
                # raise Exception("fcu_start_ts is not None")
            self.fcu_start_ts = ts

    def after_fcu(self, log, ts):
        if log['attr'] is None:
            if self.fcu_start_ts is None:
                return
            if self.fcu_no_attr_start_ts is None:
                raise Exception("fcu_no_attr_start_ts is None")
            if log['state']['headBlockHash'] != self.block_hash:
                raise Exception('block hash mismatch')
            self.fcu_no_attr_time = ts - self.fcu_no_attr_start_ts
            self.total_time = ts - self.fcu_start_ts
        else:
            if self.fcu_start_ts is None:
                raise Exception("fcu_start_ts is None")
            if self.block_ts is not None:
                print("block_ts is not None")
                # raise Exception("block_ts is not None")
            self.fcu_time = ts - self.fcu_start_ts
            self.block_ts = int(log['attr']['timestamp'], 16)

    def after_fcu_received_payload(self, log, ts):
        if int(log['attr']['timestamp'], 16) != self.block_ts:
            raise Exception('block ts mismatch')
        if self.payload_id is not None:
            print('payload_id is not None')
            #raise Exception('payload_id is not None')
        self.payload_id = log['payloadId']

    def after_fcu_inserted_block(self, log, ts):
        if log['hash'] != self.block_hash:
            raise Exception('block hash mismatch')
        if self.block_number is not None:
            raise Exception('block number is not None')
        self.block_number = log['number']
        self.result_file.write(
            BlockBuildingTime(
                self.fcu_time,
                self.get_time,
                self.new_time,
                self.fcu_no_attr_time,
                self.total_time,
                self.block_number,
                self.block_hash,
                self.gas_used_dict[self.block_hash.lower()],
            ).json() + '\n'
        )
        print(f"Processed {self.block_number}", end='\r')
        self.reset()

    def before_get(self, log, ts):
        if log['payload_id'] != self.payload_id:
            raise Exception('payload_id mismatch')
        if self.get_start_ts is not None:
            print('get_start_ts is not None')
            # raise Exception('get_start_ts is not None')
        self.get_start_ts = ts

    def after_get(self, log, ts):
        if log['payload_id'] != self.payload_id:
            raise Exception('payload_id mismatch')
        if self.get_start_ts is None:
            raise Exception('get_start_ts is None')
        self.get_time = ts - self.get_start_ts

    def before_new(self, log, ts):
        if self.block_hash is not None:
            print('block_hash is not None')
            # raise Exception('block_hash is not None')
        if self.new_start_ts is not None:
            print('new_start_ts is not None')
            # raise Exception('new_start_ts is not None')
        self.new_start_ts = ts
        self.block_hash = log['block_hash']

    def after_new(self, log, ts):
        if log['block_hash'] != self.block_hash:
            raise Exception('block_hash mismatch')
        if self.new_start_ts is None:
            raise Exception('new_start_ts is None')
        self.new_time = ts - self.new_start_ts

    def process_log(self, line):
        log = json.loads(line)
        ts_pieces = log['t'].split('.')
        ts = datetime.strptime(f'{ts_pieces[0]}.{ts_pieces[1][:-1][:3]}', "%Y-%m-%dT%H:%M:%S.%f")
        msg = log['msg']
        if msg == 'Sharing forkchoice-updated signal':
            self.before_fcu(log, ts)
        elif msg == 'Shared forkchoice-updated signal':
            self.after_fcu(log, ts)
        elif msg == 'Received payload id':
            self.after_fcu_received_payload(log, ts)
        elif msg == 'getting payload':
            self.before_get(log, ts)
        elif msg == 'Received payload':
            self.after_get(log, ts)
        elif msg == 'sending payload for execution':
            self.before_new(log, ts)
        elif msg == 'Received payload execution result':
            self.after_new(log, ts)
        elif msg == 'inserted block':
            self.after_fcu_inserted_block(log, ts)


if __name__ == '__main__':
    processor = LogProcessor()
    with open('./op-node.log', 'r') as f:
        line = f.readline()
        while line:
            try:
                processor.process_log(line)
            except Exception as e:
                print(line)
                raise e
            line = f.readline()
