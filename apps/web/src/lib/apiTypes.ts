// apps/web/src/lib/apiTypes.ts

export interface ApiErrorShape {
  status: number;
  requestId?: string;
  message: string;
  errorCode?: string;
  detail?: unknown;
}

export class ApiError extends Error implements ApiErrorShape {
  status: number;
  requestId?: string;
  errorCode?: string;
  detail?: unknown;

  constructor({ status, requestId, message, errorCode, detail }: ApiErrorShape) {
    super(message);
    this.name = "ApiError";
    // Ensure instanceof works reliably across transpilation targets
    Object.setPrototypeOf(this, ApiError.prototype);
    this.status = status;
    this.requestId = requestId;
    this.errorCode = errorCode;
    this.detail = detail;
  }
}
