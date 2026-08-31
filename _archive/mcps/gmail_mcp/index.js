/**
 * Gmail MCP Server - Silver Tier
 * Custom MCP server that exposes Gmail sending capability
 */

import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import {
    CallToolRequestSchema,
    ListToolsRequestSchema,
} from '@modelcontextprotocol/sdk/types.js';
import { GmailAutomation } from './gmail.js';
import dotenv from 'dotenv';

// Load environment variables
dotenv.config();

class GmailMCPServer {
    constructor() {
        this.server = new Server(
            {
                name: 'gmail-mcp',
                version: '1.0.0',
            },
            {
                capabilities: {
                    tools: {},
                },
            }
        );

        this.gmail = new GmailAutomation();
        this.setupToolHandlers();

        console.error('[Gmail MCP] Server initialized');
    }

    setupToolHandlers() {
        // List available tools
        this.server.setRequestHandler(ListToolsRequestSchema, async () => {
            console.error('[Gmail MCP] Tools list requested');
            return {
                tools: [
                    {
                        name: 'send_email',
                        description: 'Send an email via Gmail',
                        inputSchema: {
                            type: 'object',
                            properties: {
                                to: {
                                    type: 'string',
                                    description: 'Recipient email address',
                                },
                                subject: {
                                    type: 'string',
                                    description: 'Email subject',
                                },
                                body: {
                                    type: 'string',
                                    description: 'Email body (plain text)',
                                },
                            },
                            required: ['to', 'subject', 'body'],
                        },
                    },
                ],
            };
        });

        // Handle tool calls
        this.server.setRequestHandler(CallToolRequestSchema, async (request) => {
            console.error(`[Gmail MCP] Tool called: ${request.params.name}`);

            if (request.params.name === 'send_email') {
                const { to, subject, body } = request.params.arguments;

                try {
                    console.error(`[Gmail MCP] Sending email to: ${to}`);
                    const result = await this.gmail.sendEmail(to, subject, body);

                    console.error('[Gmail MCP] Email sent successfully');

                    return {
                        content: [
                            {
                                type: 'text',
                                text: JSON.stringify(result, null, 2),
                            },
                        ],
                    };
                } catch (error) {
                    console.error(`[Gmail MCP] Error: ${error.message}`);
                    return {
                        content: [
                            {
                                type: 'text',
                                text: `Error sending email: ${error.message}`,
                            },
                        ],
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
        console.error('[Gmail MCP] Server running on stdio');
    }

    async cleanup() {
        // Gmail API doesn't need explicit cleanup
        console.error('[Gmail MCP] Cleanup complete');
    }
}

// Main execution
const server = new GmailMCPServer();

// Handle graceful shutdown
process.on('SIGINT', async () => {
    console.error('[Gmail MCP] Shutting down...');
    await server.cleanup();
    process.exit(0);
});

process.on('SIGTERM', async () => {
    console.error('[Gmail MCP] Shutting down...');
    await server.cleanup();
    process.exit(0);
});

// Start server
server.run().catch((error) => {
    console.error('[Gmail MCP] Fatal error:', error);
    process.exit(1);
});