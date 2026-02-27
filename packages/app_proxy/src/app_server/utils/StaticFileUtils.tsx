/*
 * Copyright (C) 2026 Fluxer Contributors
 *
 * This file is part of Fluxer.
 *
 * Fluxer is free software: you can redistribute it and/or modify
 * it under the terms of the GNU Affero General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * Fluxer is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
 * GNU Affero General Public License for more details.
 *
 * You should have received a copy of the GNU Affero General Public License
 * along with Fluxer. If not, see <https://www.gnu.org/licenses/>.
 */

import {existsSync, readFileSync} from 'node:fs';
import {join} from 'node:path';
import type {CSPOptions} from '@fluxer/app_proxy/src/app_server/utils/CSP';
import {buildCSP, generateNonce} from '@fluxer/app_proxy/src/app_server/utils/CSP';
import {getMimeType, isHashedAsset} from '@fluxer/app_proxy/src/app_server/utils/Mime';
import type {Logger} from '@fluxer/logger/src/Logger';
import type {Context} from 'hono';

export function isPathSafe(filePath: string, resolvedStaticDir: string): boolean {
	return filePath.startsWith(resolvedStaticDir);
}

const STATIC_CDN_PLACEHOLDER = '{{STATIC_CDN}}';

/** Request paths that may contain {{STATIC_CDN}} and are rewritten at runtime. */
const STATIC_FILES_WITH_PLACEHOLDER = ['/manifest.json', '/browserconfig.xml'];

export interface ServeStaticFileOptions {
	requestPath: string;
	resolvedStaticDir: string;
	logger: Logger;
	/** When set, replaces {{STATIC_CDN}} in manifest.json and browserconfig.xml. */
	staticCdnEndpoint?: string;
}

export type ServeStaticFileResult =
	| {success: true; content: Buffer; mimeType: string; cacheControl: string}
	| {success: false; error?: string};

export function serveStaticFile(options: ServeStaticFileOptions): ServeStaticFileResult {
	const {requestPath, resolvedStaticDir, logger, staticCdnEndpoint} = options;
	const filePath = join(resolvedStaticDir, requestPath);

	if (!isPathSafe(filePath, resolvedStaticDir)) {
		logger.warn({requestPath, filePath}, 'directory traversal attempt blocked');
		return {success: false};
	}

	if (!existsSync(filePath)) {
		return {success: false};
	}

	try {
		const normalizedPath = requestPath.startsWith('/') ? requestPath : `/${requestPath}`;
		const shouldReplacePlaceholder =
			staticCdnEndpoint !== undefined &&
			staticCdnEndpoint !== '' &&
			STATIC_FILES_WITH_PLACEHOLDER.includes(normalizedPath);

		let content: Buffer;
		if (shouldReplacePlaceholder) {
			const text = readFileSync(filePath, 'utf-8');
			content = Buffer.from(text.replaceAll(STATIC_CDN_PLACEHOLDER, staticCdnEndpoint), 'utf-8');
		} else {
			content = readFileSync(filePath);
		}

		const mimeType = getMimeType(requestPath);
		const cacheControl = isHashedAsset(requestPath)
			? 'public, max-age=31536000, immutable'
			: 'public, max-age=3600, must-revalidate';

		return {success: true, content, mimeType, cacheControl};
	} catch (err) {
		logger.error({requestPath, error: err}, 'failed to read static file');
		return {success: false, error: 'Internal Server Error'};
	}
}

export interface ServeSpaFallbackOptions {
	resolvedStaticDir: string;
	cspDirectives?: CSPOptions;
	logger: Logger;
	/** Base URL for static CDN (scripts, fonts, favicons). Replaces {{STATIC_CDN}} in index.html. */
	staticCdnEndpoint?: string;
}

export type ServeSpaFallbackResult =
	| {success: true; content: string; nonce: string; csp: string}
	| {success: false; error: string};

export function serveSpaFallback(options: ServeSpaFallbackOptions): ServeSpaFallbackResult {
	const {resolvedStaticDir, cspDirectives, logger, staticCdnEndpoint} = options;
	const indexPath = join(resolvedStaticDir, 'index.html');

	if (!existsSync(indexPath)) {
		logger.error({path: indexPath}, 'index.html not found');
		return {success: false, error: 'Internal Server Error'};
	}

	try {
		const nonce = generateNonce();
		const csp = buildCSP(nonce, cspDirectives);

		let indexContent = readFileSync(indexPath, 'utf-8');
		indexContent = indexContent.replaceAll('{{CSP_NONCE_PLACEHOLDER}}', nonce);
		if (staticCdnEndpoint !== undefined && staticCdnEndpoint !== '') {
			indexContent = indexContent.replaceAll('{{STATIC_CDN}}', staticCdnEndpoint);
		}

		return {success: true, content: indexContent, nonce, csp};
	} catch (err) {
		logger.error({error: err}, 'failed to serve index.html');
		return {success: false, error: 'Internal Server Error'};
	}
}

export function applySpaHeaders(c: Context, csp: string): void {
	c.header('Content-Security-Policy', csp);
	c.header('Content-Type', 'text/html; charset=utf-8');
	c.header('Cache-Control', 'no-cache');
	c.header('X-Content-Type-Options', 'nosniff');
	c.header('X-Frame-Options', 'DENY');
	c.header('Referrer-Policy', 'strict-origin-when-cross-origin');
}
