"""Run the fixed pre-push subset; the complete release gate remains separate."""

from kayakgen.operations.gate import gate_entry


def main() -> int:
    return gate_entry("fast", __doc__)


if __name__ == "__main__":
    raise SystemExit(main())
