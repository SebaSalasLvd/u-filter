import { Post } from "./post";

export interface ClassifiedMessage {
  action: "postClassified";
  post: Post;
}

export type AppMessage = ClassifiedMessage;
