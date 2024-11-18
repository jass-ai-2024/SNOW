### Entities
- Document: parent, content, metadata

### Backend Functionalities
1. **Document Upload and Show List**: Allows users to upload documents in various formats.
- POST v1/documents/get_place/ - provide new path (parent id) for document based on content. in: {parent: id?, content: str, metadata: dict} out: {folder_parent_id: id, folder_name: str}
- POST v1/documents/create_folder/ - create new folder. in: {parent: id, name: str} out: {id: id}
- POST v1/documents/ - upload documents. {parent: id?, content: str, metadata: dict}
- GET v1/documents/<id> - get list of documents from parent. If there is no id for parent, return documents withour parent.

2. **Semantic Search**: Enables users to perform advanced searches using semantic understanding.
- POST v1/search/ - search in documents. in: {query: str} out: {answer: str, documents: [{id: id, parent: id, subcontent: str}]}
