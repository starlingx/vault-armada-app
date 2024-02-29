The rekey feature of Starlingx vault application performs the rekey
operation described in Hashicorp vault documentation:
https://developer.hashicorp.com/vault/tutorials/operations/rekeying-and-rotating
https://developer.hashicorp.com/vault/api-docs/v1.13.x/system/rekey

Vault rekey is intended as part of the feature to secure vault key
shards into k8s secrets, transitioning from PVC storage.  After
transitioning the existing key shards into k8s secrets vault is rekeyed
for assurance that the key shards previously stored in PVC are no
longer usable.

The rekey procedure is implemented in vault-manager's init.sh code. In
addition to Hashicorp vault's rekey procedure, the main points of the
implementation are:
 - build the procedure around verification_required option of
   /sys/rekey/init API to ensure the key shards are secure and will not
   be lost
 - perform the procedure in discrete steps, falling back to the main
   LOGIC loop to allow vault-manager to respond to requests for
   termination.

The main function rekeyVault() performs one procedure step each time it
is run.  These steps are:
  - initialize the rekey operation using API /sys/rekey/init
  - authenticate the rekey, and store the new shards
  - verify the new shards using API /sys/rekey/verify
  - shuffle the new shards into cluster-key secrets
  - audit the new shards
  - finalize the procedure, remove milestone artifacts

Three sets of k8s secrets may store shard secrets during the rekey
procedure.  Due to failures of the active server pod or vault-manager it
may be the case that at anytime during the procedure these secrets may
contain the shards the vault is actually using. During the rekey
procedure vault-manager may be using any set of these shards to unseal a
vault server that has restarted during the procedure:
  - cluster-key
  - cluster-key-bk
  - cluster-rekey

In order to manage failures of the pods during the procedure several
milestone artifacts are created after achieving the procedure steps.  In
addition to the milestones represented by k8s secrets for key shards,
the following k8s secrets are used as milestones for the procedure:
  - cluster-rekey-request:  the original request for rekey
  - cluster-rekey-verified: vault-manager receives confirmation from
                            vault server that the new shards are
                            effective
  - cluster-rekey-shuffle:  vault-manager completes the replacement of
                            key shards in cluster-key k8s secrets
  - cluster-rekey-audit:    vault-manager asserts that there hasn't been
                            a failure of the vault servers resulting in
                            the earlier confirmation being lost

The milestone artifact k8s secrets and key shard k8s secrets are used to
determine which step of the rekey procedure should progress, and to
recover from failures of the vault servers and vault-manager pods.

Validation of the rekey feature includes inducing failures of the pods
and processes.  These tests are illustrated in the
rekey_test_matrix.txt, and include variations of kubectl delete of one
or more pods, as well as killing pod processes on the platform nodes
where they are running.

