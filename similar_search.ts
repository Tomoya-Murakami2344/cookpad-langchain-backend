import * as dotenv from "dotenv";
dotenv.config();
import { OpenAIEmbeddings } from "@langchain/openai";
import { PGVectorStore } from "@langchain/community/vectorstores/pgvector";
import { PoolConfig } from "pg";

// このファイルは、livable_vectorsテーブルに格納されているベクトルと
// ユーザーの入力したクエリのベクトルの類似度を計算し、類似または関連する
// テキストを返します。

async function main(query: string) {
    // vector storeの設定
    const config = {
        postgresConnectionOptions: {
        type: "postgres",
        host: "127.0.0.1",
        port: Number(process.env.DB_PORT),
        user: process.env.DB_USER,
        password: process.env.DB_PASSWORD,
        database: process.env.DB_DATABASE,
        } as PoolConfig,
        tableName: "livable_vectors",
        columns: {
        idColumnName: "id",
        vectorColumnName: "vector",
        contentColumnName: "content",
        metadataColumnName: "metadata",
        },
    };
    const pgvectorStore = await PGVectorStore.initialize(
        new OpenAIEmbeddings(),
        config
    );
    // 類似度の高いテキスト上位3件を返す
    const results = await pgvectorStore.similaritySearch(query,3);
    console.log(results);

    await pgvectorStore.end();
}

main("マンション売却にかかる費用は？");
