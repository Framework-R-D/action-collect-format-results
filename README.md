# `action-collect-format-results`

> Aggregates results from multiple formatting jobs and produces a summary message.

## Usage

```yaml
- uses: Framework-R-D/action-collect-format-results@1e3eeee20808b0c8e754955f7633c38ff18a603d # v1
  with:
    input-name: value
```

## Inputs

| Name | Description | Required | Default |
|------|-------------|----------|---------|
| `results-json` | JSON object containing job results | true | `` |

## Outputs

| Name | Description |
|------|-------------|
| `message` | The formatted summary message |
| `has_failures` | Whether any job failed |

## License

[Apache 2.0](LICENSE)
