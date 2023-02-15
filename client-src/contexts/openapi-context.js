import {createContext} from '@lit-labs/context';
// import {DefaultApiInterface} from 'chromestatus-openapi';
// import type {DefaultApi as Api} from 'chromestatus-openapi';
// export type {DefaultApi as Api} from 'chromestatus-openapi';
/** @type {import('@lit-labs/context').Context<string, import('chromestatus-openapi').DefaultApiInterface>} */
export const chromestatusOpenApiContext = createContext('chromestatusOpenApi');
