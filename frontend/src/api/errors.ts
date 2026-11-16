import { isAxiosError } from 'axios';

import { camelizeKeys } from './case';

/** Uniform API error: `{code, message, fields, fieldCodes}` plus any extra payload keys. */
export class ApiError extends Error {
  readonly status: number;
  readonly code: string;
  readonly fields: Record<string, string[]>;
  readonly fieldCodes: Record<string, string[]>;
  readonly extra: Record<string, unknown>;

  constructor(options: {
    status: number;
    code: string;
    message?: string;
    fields?: Record<string, string[]>;
    fieldCodes?: Record<string, string[]>;
    extra?: Record<string, unknown>;
  }) {
    super(options.message ?? options.code);
    this.name = 'ApiError';
    this.status = options.status;
    this.code = options.code;
    this.fields = options.fields ?? {};
    this.fieldCodes = options.fieldCodes ?? {};
    this.extra = options.extra ?? {};
  }
}

interface ErrorBody {
  code?: string;
  message?: string;
  fields?: Record<string, string[]>;
  fieldCodes?: Record<string, string[]>;
  [key: string]: unknown;
}

export const toApiError = (error: unknown): ApiError => {
  if (error instanceof ApiError) return error;
  if (isAxiosError(error)) {
    if (!error.response) return new ApiError({ status: 0, code: 'network_error' });
    const body = camelizeKeys<ErrorBody>(error.response.data ?? {});
    const { code, message, fields, fieldCodes, ...extra } = body ?? {};
    return new ApiError({
      status: error.response.status,
      code: code ?? 'server_error',
      message,
      fields,
      fieldCodes,
      extra,
    });
  }
  return new ApiError({ status: 0, code: 'unknown_error' });
};
