const string = {type:'string'};
const strings = {type:'array',items:string};
const fields = {title:string,description:string,pause_reason:string,lessons_learned:strings,reusable_parts:strings,tags:strings,repository_url:string};
const schema = (properties:Record<string,unknown>,required:string[]=[]) => ({type:'object',properties,required,additionalProperties:false});
const annotations = (readOnlyHint:boolean) => ({readOnlyHint,destructiveHint:false,openWorldHint:false});
export const tools = [
  {name:'archive_project',description:'Save an unfinished project when the user requests archiving. Use supplied facts; never invent missing details.',inputSchema:schema(fields,['title','description','pause_reason']),annotations:annotations(false)},
  {name:'search_projects',description:'Search the current user’s archive by literal keywords. All query words must match. Empty query lists recent projects.',inputSchema:schema({query:string,status:{type:'string',enum:['archived','revived','completed']},limit:{type:'integer',minimum:1,maximum:100,default:20}}),annotations:annotations(true)},
  {name:'get_project',description:'Retrieve a full project and its revision before using it as evidence or updating it.',inputSchema:schema({project_id:string},['project_id']),annotations:annotations(true)},
  {name:'update_project',description:'Update requested fields using the revision returned by get_project. Never overwrite facts without a user request.',inputSchema:schema({project_id:string,expected_revision:{type:'integer',minimum:1},changes:schema({...fields,status:{type:'string',enum:['archived','revived','completed']}})},['project_id','expected_revision','changes']),annotations:annotations(false)},
  {name:'prepare_remix',description:'Gather 2–5 selected projects as evidence for a small new project. The assistant generates the proposal from the returned sources. Does not modify the archive.',inputSchema:schema({project_ids:{type:'array',items:string,minItems:2,maxItems:5},goal:string,time_budget_hours:{type:'integer',minimum:1,maximum:80,default:8}},['project_ids','goal']),annotations:annotations(true)},
];
