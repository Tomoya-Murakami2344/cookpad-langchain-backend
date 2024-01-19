import * as dotenv from "dotenv";
dotenv.config();
import { OpenAIEmbeddings } from "@langchain/openai";
import { PGVectorStore } from "@langchain/community/vectorstores/pgvector";
import { PoolConfig, Client} from "pg";
import { LivableText } from './mytypeorm/livable_text';
import { createConnection,getConnection,DataSource,getRepository } from "typeorm";

// First, follow set-up instructions at
// https://js.langchain.com/docs/modules/indexes/vector_stores/integrations/pgvector

// このファイルを実行すると、livable_textテーブルのtextカラムの内容を
// ベクトル化し、livable_vectorsテーブルに格納します。


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
async function main() {
    // 生のテキストがあるlivable_textテーブルへの接続
    await createConnection({
        type: "postgres",
        host: "127.0.0.1",
        port: Number(process.env.DB_PORT),
        username: process.env.DB_USER,
        password: process.env.DB_PASSWORD,
        database: process.env.DB_DATABASE,
        entities: [
            LivableText
        ],
        synchronize: false,
    });

    const userRepository = getRepository(LivableText);
    const texts = await userRepository.find({select: ["text"]});
    texts.forEach((text) => {
        // 生のテキストをベクトル化してlivable_vectorsテーブルに格納
        add_to_table(text.text, text.title);
    });
}
async function add_to_table(text: string, title: string) {
    const pgvectorStore = await PGVectorStore.initialize(
        new OpenAIEmbeddings(),
        config
    );

    await pgvectorStore.addDocuments([
        { pageContent: text, metadata: { title: title }}
    ]);

    await pgvectorStore.end();
}

main();
