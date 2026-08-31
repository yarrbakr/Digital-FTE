/**
 * LinkedIn MCP Server - Silver Tier
 * Exposes LinkedIn posting capability via MCP protocol
 */

import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import {
    CallToolRequestSchema,
    ListToolsRequestSchema,
} from '@modelcontextprotocol/sdk/types.js';
import { LinkedInAutomation } from './linkedin.js';
import dotenv from 'dotenv';

dotenv.config();

class LinkedInMCPServer {
    constructor() {
        this.server = new Server(
            { name: 'linkedin-mcp', version: '1.0.0' },
            { capabilities: { tools: {} } }
        );
        this.linkedin = new LinkedInAutomation();
        this.setupToolHandlers();
    }

    setupToolHandlers() {
        this.server.setRequestHandler(ListToolsRequestSchema, async () => ({
            tools: [
                {
                    name: 'post_to_linkedin',
                    description: 'Post content to LinkedIn',
                    inputSchema: {
                        type: 'object',
                        properties: {
                            content: { type: 'string', description: 'Text to post' },
                        },
                        required: ['content'],
                    },
                },
            ],
        }));

        this.server.setRequestHandler(CallToolRequestSchema, async (request) => {
            if (request.params.name === 'post_to_linkedin') {
                try {
                    const result = await this.linkedin.createPost(
                        request.params.arguments.content
                    );
                    return {
                        content: [{ type: 'text', text: JSON.stringify(result, null, 2) }],
                    };
                } catch (error) {
                    return {
                        content: [{ type: 'text', text: `Error: ${error.message}` }],
                        isError: true,
                    };
                }
            }
            throw new Error(`Unknown tool: ${request.params.name}`);
        });
    }

    async run() {
        const transport = new StdioServerTransport();
        await this.server.connect(transport);
        console.error('[LinkedIn MCP] Server running');
    }
}

const server = new LinkedInMCPServer();
server.run().catch((error) => {
    console.error('[LinkedIn MCP] Fatal error:', error);
    process.exit(1);
});

process.on('SIGINT', async () => {
    await server.linkedin.close();
    process.exit(0);
});