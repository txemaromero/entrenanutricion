import { fireEvent, render, screen } from '@testing-library/react';

import { ApiError } from '../../api/errors';
import i18n from '../../i18n';
import { uploadError } from '../../utils/errors';
import { MediaPicker } from './MediaPicker';

const TOO_MANY_PIXELS = 'La imagen tiene demasiados píxeles (hasta 40 megapíxeles).';

const refused = (field: string) =>
  new ApiError({
    status: 400,
    code: 'validation_error',
    fields: { [field]: ['Images must be 40 megapixels or smaller.'] },
    fieldCodes: { [field]: ['image_too_large'] },
  });

describe('files refused by the API', () => {
  it('finds the error of the file, whatever the field is called', () => {
    for (const field of ['photo', 'media', 'file']) {
      expect(uploadError(i18n.t, refused(field))).toBe(TOO_MANY_PIXELS);
    }
    expect(uploadError(i18n.t, refused('name'))).toBeUndefined();
    expect(uploadError(i18n.t, new Error('offline'))).toBeUndefined();
  });

  it('the picker shows it, and its own check first when a new file is wrong', () => {
    render(
      <MediaPicker
        label="Portada"
        currentUrl={null}
        currentKind={null}
        value={{ remove: false }}
        onChange={() => undefined}
        serverError={TOO_MANY_PIXELS}
      />,
    );
    expect(screen.getByTestId('media-error')).toHaveTextContent(TOO_MANY_PIXELS);

    const gif = new File(['GIF89a'], 'animada.gif', { type: 'image/gif' });
    fireEvent.change(screen.getByTestId('media-input'), { target: { files: [gif] } });

    expect(screen.getByTestId('media-error')).toHaveTextContent(
      'Tipo de archivo no permitido (JPG, PNG, WEBP o MP4).',
    );
  });
});
