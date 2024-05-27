# Block Building Statistics

Measure block building time of base-mainnet history blocks and calculate distributions

## Test Construction
### Machine
AWS [i3en.3xlarge](https://aws.amazon.com/ko/ec2/instance-types/i3en/), 1 node per 1 machine

12 vCPU, 96GiB Memory, 1 x 7500 NVMe SSD

### Node Version
- op-node: https://github.com/testinprod-io/optimism/tree/engine-api-timing
  - Based on [op-node/v1.7.5](https://github.com/ethereum-optimism/optimism/releases/tag/op-node%2Fv1.7.5)
  - Only changed engine API timing logs to Debug level.([0c820a9](https://github.com/ethereum-optimism/optimism/commit/0c820a9c0bfa3f33bf2cff8f4712b48409fce8bd))
- op-geth: [v1.101315.0](https://github.com/ethereum-optimism/op-geth/releases/tag/v1.101315.0)
- op-reth: [v0.2.0-beta.7](https://github.com/paradigmxyz/reth/releases/tag/v0.2.0-beta.7)
  - Built with `make maxperf-op`

### Node Configs
- op-node
  ```shell
  /home/ubuntu/optimism/op-node/bin/op-node \
    --l1=$L1_ENDPOINT \
    --l1.beacon=$L1_BEACON_ENDPOINT \
    --l2=$L2_ENDPOINT \
    --l2.jwt-secret=$JWT_SECRET \
    --network=base-mainnet \
    --verifier.l1-confs=0 \
    --rpc.addr=127.0.0.1 \
    --rpc.port=9545 \
    --p2p.listen.ip=0.0.0.0 \
    --l1.trustrpc=true \
    --log.format=json \
    --log.level=debug \
    --p2p.discovery.path=$P2P_DISCOVERY_DB \
    --p2p.peerstore.path=$P2P_DISCOVERY_DB \
    --p2p.disable=true \
    --l1.rpckind=erigon 2>&1 | tee /mnt/nvme/logs/op-node.log
  ```

- op-geth
  ```shell
  /home/ubuntu/op-geth/build/bin/geth \
    --datadir=$OP_GETH_DB \
    --http \
    --http.addr=127.0.0.1 \
    --http.port=8545 \
    --http.corsdomain=* \
    --http.vhosts=* \
    --authrpc.addr=127.0.0.1 \
    --authrpc.port=8551 \
    --authrpc.vhosts=* \
    --rollup.disabletxpoolgossip=true \
    --http.api=eth,admin,debug \
    --authrpc.jwtsecret=$JWT_SECRET \
    --op-network=base-mainnet \
    --gcmode=$GCMODE \
    --verbosity=4 \
    --nodiscover \
    --cache=8192 \
    --log.format=json \
    --log.file=/mnt/nvme/logs/op-geth.log
  ```
  - `GCMODE` is `archive` for archive nodes and `full` for full nodes

- op-reth
  - command
    ```shell
    op-reth node \
      --chain base \
      --rollup.sequencer-http https://mainnet-sequencer.base.org \
      --http \
      --ws \
      --authrpc.port 8551 \
      --authrpc.jwtsecret $JWT_SECRET \
      --disable-discovery \
      --datadir $OP_RETH_DB \
      --log.file.format json \
      --log.file.directory /mnt/nvme/logs \
      --log.file.max-size 2024 \
      --log.file.max-files 1000 \
      --config /home/ubuntu/reth.toml
      -vvvv
    ```
  - config
    ```toml
    [prune]
    block_interval = 999999999
    ```
    - This is to fix https://github.com/paradigmxyz/reth/issues/7500

### Test Method
1. Run op-node and op-geth/op-reth.
2. Derive base-mainnet chain from L1.
3. Left engine API timing logs of op-node.
4. Parse op-node logs to measure block building time.
   1. Definition of Block building time:
      - op-node calls 4 engine API requests to build a block: `FCU` - `GetPayload` - `NewPayload` - `FCU`.
      - `total_time` = last `FCU`'s [response timestamp](https://github.com/ethereum-optimism/optimism/commit/0c820a9c0bfa3f33bf2cff8f4712b48409fce8bd#diff-24782d08763abbaa332e4288033227ac3da7d4ba75246c5aadbfa422392473f1R93) - first `FCU`'s [request timestamp](https://github.com/ethereum-optimism/optimism/commit/0c820a9c0bfa3f33bf2cff8f4712b48409fce8bd#diff-24782d08763abbaa332e4288033227ac3da7d4ba75246c5aadbfa422392473f1R86)
      - This definition is almost equal to Base's [benchmark](https://github.com/danyalprout/replayor/blob/main/packages/replayor/benchmark.go#L214)
   2. `python parse_logs.py`
3. Calculate result distribution by `stats.ipynb`

### Data Set
Measure block building time for following cases
- op-geth
  - Archive node from genesis
  - Full node from genesis
  - Archive node from snapshot(`base-mainnet-archive-1714488087.tar.gz`)
  - Full node from snapshot(`base-mainnet-full-1715926911.tar.gz`)
- op-reth
  - Archive node from genesis
