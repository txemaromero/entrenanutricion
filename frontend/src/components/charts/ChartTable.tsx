/** The values of a chart as a table for screen readers (the canvas only has a summary label). */
export const ChartTable = ({
  caption,
  labels,
  values,
  rowTestId,
}: {
  caption: string;
  labels: string[];
  values: string[];
  rowTestId?: string;
}) => (
  <table className="visually-hidden">
    <caption>{caption}</caption>
    <tbody>
      {labels.map((label, index) => (
        <tr key={`${label}-${index}`} data-testid={rowTestId}>
          <th scope="row">{label}</th>
          <td>{values[index]}</td>
        </tr>
      ))}
    </tbody>
  </table>
);
