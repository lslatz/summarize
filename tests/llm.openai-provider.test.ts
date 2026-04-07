import { describe, expect, it, vi } from "vitest";
import { buildMinimalPdf } from "./helpers/pdf.js";

const mocks = vi.hoisted(() => ({
  completeSimple: vi.fn(),
}));

vi.mock("@mariozechner/pi-ai", () => ({
  completeSimple: mocks.completeSimple,
}));

import {
  completeOpenAiDocument,
  completeOpenAiText,
  resolveOpenAiClientConfig,
} from "../src/llm/providers/openai.js";

describe("openai provider helpers", () => {
  it("resolves openrouter config from keys and forced mode", () => {
    expect(
      resolveOpenAiClientConfig({
        apiKeys: {
          openaiApiKey: null,
          openrouterApiKey: "or-key",
        },
      }),
    ).toEqual({
      apiKey: "or-key",
      baseURL: "https://openrouter.ai/api/v1",
      useChatCompletions: true,
      isOpenRouter: true,
    });

    expect(
      resolveOpenAiClientConfig({
        apiKeys: {
          openaiApiKey: "oa-key",
          openrouterApiKey: null,
        },
        forceOpenRouter: true,
      }),
    ).toEqual({
      apiKey: "oa-key",
      baseURL: "https://openrouter.ai/api/v1",
      useChatCompletions: true,
      isOpenRouter: true,
    });
  });

  it("handles custom and invalid base URLs", () => {
    expect(
      resolveOpenAiClientConfig({
        apiKeys: {
          openaiApiKey: "oa-key",
          openrouterApiKey: null,
        },
        openaiBaseUrlOverride: "https://gateway.example/v1",
      }),
    ).toEqual({
      apiKey: "oa-key",
      baseURL: "https://gateway.example/v1",
      useChatCompletions: true,
      isOpenRouter: false,
    });

    expect(
      resolveOpenAiClientConfig({
        apiKeys: {
          openaiApiKey: "oa-key",
          openrouterApiKey: null,
        },
        openaiBaseUrlOverride: "not a url",
      }),
    ).toEqual({
      apiKey: "oa-key",
      baseURL: "not a url",
      useChatCompletions: false,
      isOpenRouter: false,
    });
  });

  it("raises missing key errors for OpenAI and OpenRouter modes", () => {
    expect(() =>
      resolveOpenAiClientConfig({
        apiKeys: {
          openaiApiKey: null,
          openrouterApiKey: null,
        },
      }),
    ).toThrow(/Missing OPENAI_API_KEY/);

    expect(() =>
      resolveOpenAiClientConfig({
        apiKeys: {
          openaiApiKey: null,
          openrouterApiKey: null,
        },
        forceOpenRouter: true,
      }),
    ).toThrow(/Missing OPENROUTER_API_KEY/);
  });

  it("builds OpenAI document response URLs for /responses, /v1, and root bases", async () => {
    const pdfBytes = buildMinimalPdf("Hello PDF");
    const fetchMock = vi.fn(async () => {
      return new Response(
        JSON.stringify({
          output: [{ content: [{ text: "ok" }] }],
          usage: { input_tokens: 1, output_tokens: 2, total_tokens: 3 },
        }),
        { status: 200, headers: { "content-type": "application/json" } },
      );
    });

    const promptText = "Summarize";
    const document = {
      kind: "document" as const,
      bytes: pdfBytes,
      filename: "test.pdf",
      mediaType: "application/pdf",
    };

    for (const baseURL of [
      "https://api.openai.com/responses",
      "https://api.openai.com/v1",
      "https://api.openai.com",
    ]) {
      const result = await completeOpenAiDocument({
        modelId: "gpt-5.2",
        openaiConfig: {
          apiKey: "oa-key",
          baseURL,
          useChatCompletions: true,
          isOpenRouter: false,
        },
        promptText,
        document,
        timeoutMs: 2000,
        fetchImpl: fetchMock as unknown as typeof fetch,
      });

      expect(result.text).toBe("ok");
    }

    expect(fetchMock.mock.calls.map((call) => String(call[0]))).toEqual([
      "https://api.openai.com/responses",
      "https://api.openai.com/v1/responses",
      "https://api.openai.com/v1/responses",
    ]);
  });

  it("rejects unsupported document attachment backends", async () => {
    const pdfBytes = buildMinimalPdf("Hello PDF");
    const document = {
      kind: "document" as const,
      bytes: pdfBytes,
      filename: "test.pdf",
      mediaType: "application/pdf",
    };

    await expect(
      completeOpenAiDocument({
        modelId: "gpt-5.2",
        openaiConfig: {
          apiKey: "oa-key",
          baseURL: "https://openrouter.ai/api/v1",
          useChatCompletions: true,
          isOpenRouter: true,
        },
        promptText: "Summarize",
        document,
        timeoutMs: 2000,
        fetchImpl: globalThis.fetch.bind(globalThis),
      }),
    ).rejects.toThrow(/OpenRouter does not support PDF attachments/);

    await expect(
      completeOpenAiDocument({
        modelId: "gpt-5.2",
        openaiConfig: {
          apiKey: "oa-key",
          baseURL: "https://gateway.example/v1",
          useChatCompletions: true,
          isOpenRouter: false,
        },
        promptText: "Summarize",
        document,
        timeoutMs: 2000,
        fetchImpl: globalThis.fetch.bind(globalThis),
      }),
    ).rejects.toThrow(/Document attachments require api.openai.com/);
  });

  it("rejects non-document attachments for the document API", async () => {
    await expect(
      completeOpenAiDocument({
        modelId: "gpt-5.2",
        openaiConfig: {
          apiKey: "oa-key",
          baseURL: "https://api.openai.com/v1",
          useChatCompletions: true,
          isOpenRouter: false,
        },
        promptText: "Summarize",
        document: {
          kind: "image",
          bytes: new Uint8Array([1, 2, 3]),
          filename: "test.png",
          mediaType: "image/png",
        },
        timeoutMs: 2000,
        fetchImpl: globalThis.fetch.bind(globalThis),
      }),
    ).rejects.toThrow(/expected a document attachment/);
  });

  it("surfaces document API failures and empty document outputs", async () => {
    const pdfBytes = buildMinimalPdf("Hello PDF");
    const document = {
      kind: "document" as const,
      bytes: pdfBytes,
      filename: "test.pdf",
      mediaType: "application/pdf",
    };

    await expect(
      completeOpenAiDocument({
        modelId: "gpt-5.2",
        openaiConfig: {
          apiKey: "oa-key",
          baseURL: "https://api.openai.com/v1",
          useChatCompletions: true,
          isOpenRouter: false,
        },
        promptText: "Summarize",
        document,
        timeoutMs: 2000,
        fetchImpl: (async () =>
          new Response(JSON.stringify({ error: "boom" }), { status: 500 })) as typeof fetch,
      }),
    ).rejects.toThrow(/OpenAI API error \(500\)/);

    await expect(
      completeOpenAiDocument({
        modelId: "gpt-5.2",
        openaiConfig: {
          apiKey: "oa-key",
          baseURL: "https://api.openai.com/v1",
          useChatCompletions: true,
          isOpenRouter: false,
        },
        promptText: "Summarize",
        document,
        timeoutMs: 2000,
        fetchImpl: (async () =>
          new Response(JSON.stringify({ output: [{ content: [{ text: "   " }] }] }), {
            status: 200,
          })) as typeof fetch,
      }),
    ).rejects.toThrow(/empty summary/);
  });

  it("reads GitHub chat completion arrays and rejects empty results", async () => {
    const fetchMock = vi
      .fn()
      .mockImplementationOnce(async () => {
        return new Response(
          JSON.stringify({
            choices: [
              {
                message: {
                  content: [
                    { type: "text", text: "Hello" },
                    { type: "text", text: " world" },
                  ],
                },
              },
            ],
            usage: { prompt_tokens: 1, completion_tokens: 2, total_tokens: 3 },
          }),
          { status: 200, headers: { "content-type": "application/json" } },
        );
      })
      .mockImplementationOnce(async () => {
        return new Response(
          JSON.stringify({
            choices: [{ message: { content: [{ type: "image", image_url: "x" }] } }],
          }),
          { status: 200, headers: { "content-type": "application/json" } },
        );
      });

    const originalFetch = globalThis.fetch;
    vi.stubGlobal("fetch", fetchMock);
    try {
      const context = {
        systemPrompt: "system",
        messages: [
          { role: "user" as const, content: "hello" },
          {
            role: "assistant" as const,
            content: [{ type: "text" as const, text: "seen" }],
          },
        ],
      };

      const result = await completeOpenAiText({
        modelId: "openai/gpt-4.1",
        openaiConfig: {
          apiKey: "gh-key",
          baseURL: "https://models.github.ai/inference",
          useChatCompletions: true,
          isOpenRouter: false,
          extraHeaders: { Accept: "application/vnd.github+json" },
        },
        context,
        signal: new AbortController().signal,
      });

      expect(result.text).toBe("Hello world");

      await expect(
        completeOpenAiText({
          modelId: "openai/gpt-4.1",
          openaiConfig: {
            apiKey: "gh-key",
            baseURL: "https://models.github.ai/inference",
            useChatCompletions: true,
            isOpenRouter: false,
          },
          context,
          signal: new AbortController().signal,
        }),
      ).rejects.toThrow(/empty summary/);
    } finally {
      globalThis.fetch = originalFetch;
    }
  });

  it("surfaces GitHub chat completion HTTP errors", async () => {
    const originalFetch = globalThis.fetch;
    vi.stubGlobal(
      "fetch",
      vi.fn(async () => new Response(JSON.stringify({ error: "denied" }), { status: 403 })),
    );
    try {
      await expect(
        completeOpenAiText({
          modelId: "openai/gpt-4.1",
          openaiConfig: {
            apiKey: "gh-key",
            baseURL: "https://models.github.ai/inference",
            useChatCompletions: true,
            isOpenRouter: false,
          },
          context: {
            systemPrompt: null,
            messages: [{ role: "user", content: "hello" }],
          },
          signal: new AbortController().signal,
        }),
      ).rejects.toThrow(/OpenAI API error \(403\)/);
    } finally {
      globalThis.fetch = originalFetch;
    }
  });
});
