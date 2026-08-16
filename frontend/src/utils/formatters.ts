export function formatLeaning(value: number) {
  if (value <= -0.34) return `Left (${value.toFixed(1)})`;
  if (value >= 0.34) return `Right (${value.toFixed(1)})`;
  return `Center (${value.toFixed(1)})`;
}
