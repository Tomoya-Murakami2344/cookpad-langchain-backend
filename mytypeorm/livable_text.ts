import { Entity, PrimaryGeneratedColumn, Column } from "typeorm";

@Entity("livable_text")
export class LivableText {
    @PrimaryGeneratedColumn()
    id: number;

    @Column()
    url: string;

    @Column()
    title: string;

    @Column()
    text: string;

    constructor(url: string, title: string, text: string) {
        this.url = url;
        this.title = title;
        this.text = text;
    }
}