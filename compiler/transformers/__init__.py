"""
JOCKY Compiler — IR Transformation Engine
Phase 8: Build diversification through safe semantic-preserving transformations.
"""
import copy
import hashlib
import random
import uuid
from datetime import datetime
from typing import List

from compiler.ir import IRProgram, IRNode, IRScope, OpCode


class BaseTransformer:
    """Abstract base for all IR transformers."""
    name: str = "base"

    def transform(self, ir: IRProgram) -> IRProgram:
        raise NotImplementedError

    def _deep_copy(self, ir: IRProgram) -> IRProgram:
        return copy.deepcopy(ir)


# ─────────────────────────────────────────────────────────────────────
# Transformation 1: Identifier Renaming
# Renames internal op names to equivalent aliases for a variant build.
# ─────────────────────────────────────────────────────────────────────

IDENTIFIER_ALIASES = {
    "COLLECT": ["FETCH", "ENUM", "GATHER", "ACQUIRE"],
    "ANALYZE": ["INSPECT", "SCAN", "EXAMINE", "ASSESS"],
    "FILTER": ["APPLY_FILTER", "REDUCE", "SELECT"],
    "GENERATE_TIMELINE": ["BUILD_TIMELINE", "EMIT_TIMELINE", "CONSTRUCT_TIMELINE"],
    "GENERATE_REPORT": ["EMIT_REPORT", "BUILD_REPORT", "OUTPUT_REPORT"],
    "BEGIN_SCOPE": ["ENTER_SCOPE", "OPEN_SCOPE"],
    "END_SCOPE": ["EXIT_SCOPE", "CLOSE_SCOPE"],
}


class IdentifierRenamer(BaseTransformer):
    name = "identifier_rename"
    _seed = 42

    def transform(self, ir: IRProgram) -> IRProgram:
        result = self._deep_copy(ir)
        rng = random.Random(self._seed)

        def rename_op(op: IRNode) -> IRNode:
            aliases = IDENTIFIER_ALIASES.get(op.op)
            if aliases:
                op.op = rng.choice(aliases)
                op.metadata["_original_op"] = op.op
            return op

        for scope in result.scopes:
            scope.operations = [rename_op(op) for op in scope.operations]
        result.global_ops = [rename_op(op) for op in result.global_ops]
        return result


# ─────────────────────────────────────────────────────────────────────
# Transformation 2: Operation Reordering
# Reorders independent operations while preserving data dependencies.
# ─────────────────────────────────────────────────────────────────────

# Collect ops are independent of each other — safe to reorder
# Analyze/Filter/Generate depend on preceding Collect — must stay after
_COLLECT_OPS = {"COLLECT", "FETCH", "ENUM", "GATHER", "ACQUIRE"}
_ANALYZE_OPS = {"ANALYZE", "INSPECT", "SCAN", "EXAMINE", "ASSESS"}
_FILTER_OPS  = {"FILTER", "APPLY_FILTER", "REDUCE", "SELECT"}
_GEN_OPS     = {"GENERATE_TIMELINE", "BUILD_TIMELINE", "GENERATE_REPORT", "EMIT_REPORT",
                "EMIT_TIMELINE", "CONSTRUCT_TIMELINE", "BUILD_REPORT", "OUTPUT_REPORT"}


class OperationReorderer(BaseTransformer):
    name = "operation_reorder"
    _seed = 7

    def transform(self, ir: IRProgram) -> IRProgram:
        result = self._deep_copy(ir)
        rng = random.Random(self._seed)

        def reorder(ops: List[IRNode]) -> List[IRNode]:
            collects = [op for op in ops if op.op in _COLLECT_OPS]
            rest = [op for op in ops if op.op not in _COLLECT_OPS]
            rng.shuffle(collects)
            return collects + rest

        for scope in result.scopes:
            scope.operations = reorder(scope.operations)
        if result.global_ops:
            result.global_ops = reorder(result.global_ops)
        return result


# ─────────────────────────────────────────────────────────────────────
# Transformation 3: Constant Representation
# Rewrites constant values into equivalent forms in metadata.
# ─────────────────────────────────────────────────────────────────────

class ConstantRepresenter(BaseTransformer):
    name = "constant_representation"

    def transform(self, ir: IRProgram) -> IRProgram:
        result = self._deep_copy(ir)

        def transform_args(args: dict) -> dict:
            new_args = {}
            for k, v in args.items():
                if isinstance(v, int):
                    # Represent as hex string equivalent
                    new_args[k] = v
                    new_args[f"_{k}_hex"] = hex(v)
                elif isinstance(v, str) and len(v) > 4:
                    new_args[k] = v
                    new_args[f"_{k}_hash"] = hashlib.md5(v.encode()).hexdigest()[:8]
                else:
                    new_args[k] = v
            return new_args

        for scope in result.scopes:
            for op in scope.operations:
                if op.arguments:
                    op.arguments = transform_args(op.arguments)
        return result


# ─────────────────────────────────────────────────────────────────────
# Transformation 4: Metadata Variation
# Injects different build metadata (UUID, timestamp, etc.)
# ─────────────────────────────────────────────────────────────────────

class MetadataVariator(BaseTransformer):
    name = "metadata_variation"

    def __init__(self, profile: str = "forensic_standard"):
        self.profile = profile

    def transform(self, ir: IRProgram) -> IRProgram:
        result = self._deep_copy(ir)
        build_uuid = str(uuid.uuid4())
        ts = datetime.utcnow().isoformat()

        def add_meta(op: IRNode) -> IRNode:
            op.metadata.update({
                "build_uuid": build_uuid,
                "build_ts": ts,
                "profile": self.profile,
                "transform_seq": hashlib.sha1(
                    (op.op + build_uuid).encode()
                ).hexdigest()[:12],
            })
            return op

        for scope in result.scopes:
            scope.operations = [add_meta(op) for op in scope.operations]
        result.global_ops = [add_meta(op) for op in result.global_ops]
        return result


# ─────────────────────────────────────────────────────────────────────
# Transformation 5: Profile Selector
# Combines transformers based on build profile.
# ─────────────────────────────────────────────────────────────────────

PROFILES = {
    "forensic_standard": [ConstantRepresenter, MetadataVariator],
    "forensic_hardened": [IdentifierRenamer, ConstantRepresenter, MetadataVariator],
    "forensic_variant":  [IdentifierRenamer, OperationReorderer, ConstantRepresenter, MetadataVariator],
}


class ProfileSelector:
    def __init__(self, profile: str = "forensic_standard"):
        self.profile = profile
        transformer_classes = PROFILES.get(profile, PROFILES["forensic_standard"])
        self.pipeline: List[BaseTransformer] = [
            cls(profile) if cls == MetadataVariator else cls()
            for cls in transformer_classes
        ]

    def apply(self, ir: IRProgram) -> tuple[IRProgram, list[str]]:
        """Apply all transformers in sequence. Returns (transformed_ir, transformation_log)."""
        log = []
        result = ir
        for transformer in self.pipeline:
            result = transformer.transform(result)
            log.append(transformer.name)
        return result, log
