import { fireEvent, render, screen, waitFor } from '@testing-library/react';

import type { Note } from '../../api/types';
import { NotesThread } from './NotesThread';

const note = (overrides: Partial<Note>): Note => ({
  id: 1,
  body: 'Hola',
  authorName: 'Lucía Fernández',
  authorRole: 'client',
  fromClient: true,
  createdAt: '2026-03-02T10:00:00Z',
  readAt: null,
  ...overrides,
});

// Newest first, as the API returns them.
const NOTES = [
  note({
    id: 3,
    body: 'Baja la profundidad',
    authorName: 'Marc Vidal',
    authorRole: 'trainer',
    fromClient: false,
  }),
  note({ id: 2, body: '¿Lo hago igual?', readAt: '2026-03-02T12:00:00Z' }),
];

const typeInto = (value: string) =>
  fireEvent(
    screen.getByTestId('note-body'),
    new CustomEvent('ionInput', { detail: { value }, bubbles: true }),
  );

describe('NotesThread', () => {
  it('shows the thread oldest first with the own side on the right', () => {
    render(<NotesThread notes={NOTES} viewer="client" onSend={vi.fn()} />);

    const items = screen.getAllByTestId(/^note-\d+$/);
    expect(items.map((item) => item.dataset.testid)).toEqual(['note-2', 'note-3']);
    expect(screen.getByTestId('note-2')).toHaveAttribute('data-mine', 'true');
    expect(screen.getByTestId('note-2')).toHaveTextContent('Tú ·');
    expect(screen.getByTestId('note-3')).toHaveTextContent('Marc Vidal (Entrenador)');
    // The team's note has not been read yet.
    expect(screen.getByTestId('note-3')).toHaveTextContent('Nueva');
    expect(screen.getAllByTestId('note-new')).toHaveLength(1);
  });

  it('the staff sees the client on the left', () => {
    render(<NotesThread notes={NOTES} viewer="staff" onSend={vi.fn()} />);

    expect(screen.getByTestId('note-2')).toHaveAttribute('data-mine', 'false');
    expect(screen.getByTestId('note-2')).toHaveTextContent('Lucía Fernández ·');
    expect(screen.getByTestId('note-3')).toHaveAttribute('data-mine', 'true');
  });

  it('sends the text and clears the box', async () => {
    const onSend = vi.fn().mockResolvedValue(undefined);
    render(<NotesThread notes={[]} viewer="client" onSend={onSend} />);
    expect(screen.getByTestId('notes-empty')).toBeInTheDocument();

    typeInto('  ¿Cuándo empiezo?  ');
    fireEvent.submit(screen.getByTestId('send-note').closest('form')!);

    await waitFor(() => expect(onSend).toHaveBeenCalledWith('¿Cuándo empiezo?'));
    await waitFor(() => expect(screen.getByTestId('note-body')).toHaveProperty('value', ''));
  });

  it('an empty note is not sent', async () => {
    const onSend = vi.fn();
    render(<NotesThread notes={[]} viewer="staff" onSend={onSend} />);

    typeInto('   ');
    fireEvent.submit(screen.getByTestId('send-note').closest('form')!);

    await waitFor(() =>
      expect(screen.getByTestId('note-body')).toHaveAttribute('aria-invalid', 'true'),
    );
    expect(onSend).not.toHaveBeenCalled();
  });
});
