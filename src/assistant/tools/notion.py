import json
from notion_client import Client
from notion_client.errors import APIResponseError

class Notion:
    def __init__(self, api_token: str, databases: dict = None):
        if not api_token:
            raise ValueError("Notion API token is required and was not provided.")
        self.api_token = api_token
        self.databases = databases or {}
        
        self.client = Client(auth=self.api_token)

    def get_database_id(self, database_name: str) -> str:
        """Get the database ID based on the given database name."""
        if not database_name:
            return None
        
        return self.databases.get(database_name)

    def list_available_databases(self) -> dict:
        """Return a list of available database names and their IDs."""
        return {
            "available_databases": list(self.databases.keys()),
            "message": "Use one of these database names when working with Notion databases."
        }

    def create_page(self, page_title: str, 
                  database_name: str = None, 
                  parent_database_id: str = None, 
                  parent_page_id: str = None, 
                  properties_json: str = None, 
                  content_blocks_json: str = None) -> dict:
        """Create a new page in Notion with the specified parent and properties."""
        if not page_title:
            return {"error": True, "message": "Page title is required."}

        properties = {}
        parent = {}

        if parent_database_id:
            parent = {"database_id": parent_database_id}
        elif database_name:
            database_id = self.get_database_id(database_name)
            if database_id:
                parent = {"database_id": database_id}
            else:
                available_dbs = ", ".join(self.databases.keys())
                return {
                    "error": True, 
                    "message": f"Database name '{database_name}' not found. Available databases: {available_dbs}"
                }
        elif parent_page_id:
            parent = {"page_id": parent_page_id}
        else:
            available_dbs = ", ".join(self.databases.keys())
            return {
                "error": True, 
                "message": f"A parent (database_name, parent_database_id, or parent_page_id) must be specified. Available databases: {available_dbs}"
            }

        if "database_id" in parent:
            properties["title"] = {
                "title": [{"text": {"content": page_title}}]
            }
            
            if properties_json:
                try:
                    additional_properties = json.loads(properties_json)
                    if "title" in additional_properties:
                        del additional_properties["title"]  # Avoid overriding the main title
                    properties.update(additional_properties)
                except json.JSONDecodeError:
                    return {"error": True, "message": "Invalid JSON string for properties_json when parent is a database."}
        else:
            properties["title"] = {
                "title": [{"text": {"content": page_title}}]
            }
            if properties_json:
                return {"error": True, "message": "properties_json is not applicable when parent is a page. Only page_title is used."}

        page_data = {
            "parent": parent,
            "properties": properties
        }

        if content_blocks_json:
            try:
                children = json.loads(content_blocks_json)
                page_data["children"] = children
            except json.JSONDecodeError:
                return {"error": True, "message": "Invalid JSON string for content_blocks_json."}
        
        try:
            response = self.client.pages.create(**page_data)
            return response
        except APIResponseError as e:
            return {
                "error": True,
                "status_code": e.code,
                "message": e.message
            }
        except Exception as e:
            return {"error": True, "message": str(e)}

    def query_database(self, database_name: str = None, database_id: str = None, filter_json: str = None, sorts_json: str = None) -> dict:
        """Query a database for pages based on optional filters and sorts."""
        db_id_to_use = None
        
        if database_id:
            db_id_to_use = database_id
        elif database_name:
            db_id_to_use = self.get_database_id(database_name)
            if not db_id_to_use:
                available_dbs = ", ".join(self.databases.keys())
                return {
                    "error": True, 
                    "message": f"Database name '{database_name}' not found. Available databases: {available_dbs}"
                }
        else:
            available_dbs = ", ".join(self.databases.keys())
            return {
                "error": True, 
                "message": f"Either database_name or database_id must be provided. Available databases: {available_dbs}"
            }

        query_params = {"database_id": db_id_to_use}
        
        if filter_json:
            try:
                query_params["filter"] = json.loads(filter_json)
            except json.JSONDecodeError:
                return {"error": True, "message": "Invalid JSON string for filter_json."}
        
        if sorts_json:
            try:
                query_params["sorts"] = json.loads(sorts_json)
            except json.JSONDecodeError:
                return {"error": True, "message": "Invalid JSON string for sorts_json."}
        
        try:
            response = self.client.databases.query(**query_params)
            return response
        except APIResponseError as e:
            return {
                "error": True,
                "status_code": e.code,
                "message": e.message
            }
        except Exception as e:
            return {"error": True, "message": str(e)}

    def add_content_to_page(self, page_id: str, content_blocks_json: str) -> dict:
        """Add content blocks to an existing page."""
        if not page_id:
            return {"error": True, "message": "Page ID is required to add content."}
        if not content_blocks_json:
            return {"error": True, "message": "content_blocks_json is required."}
            
        try:
            children = json.loads(content_blocks_json)
            
            response = self.client.blocks.children.append(
                block_id=page_id,
                children=children
            )
            return response
        except json.JSONDecodeError:
            return {"error": True, "message": "Invalid JSON string for content_blocks_json."}
        except APIResponseError as e:
            return {
                "error": True,
                "status_code": e.code,
                "message": e.message
            }
        except Exception as e:
            return {"error": True, "message": str(e)}

    def get_page_content(self, page_id: str) -> dict:
        """Retrieve all blocks (content) for a given page."""
        if not page_id:
            return {"error": True, "message": "Page ID is required to get content."}
        
        try:
            response = self.client.blocks.children.list(block_id=page_id)
            return response
        except APIResponseError as e:
            return {
                "error": True,
                "status_code": e.code,
                "message": e.message
            }
        except Exception as e:
            return {"error": True, "message": str(e)}

    def update_page_properties(self, page_id: str, properties_json: str) -> dict:
        """Update properties of an existing page."""
        if not page_id:
            return {"error": True, "message": "Page ID is required to update properties."}
        if not properties_json:
            return {"error": True, "message": "properties_json is required."}

        try:
            properties = json.loads(properties_json)
            
            response = self.client.pages.update(
                page_id=page_id,
                properties=properties
            )
            return response
        except json.JSONDecodeError:
            return {"error": True, "message": "Invalid JSON string for properties_json."}
        except APIResponseError as e:
            return {
                "error": True, 
                "status_code": e.code,
                "message": e.message
            }
        except Exception as e:
            return {"error": True, "message": str(e)}

    def process(self, mode: str, **kwargs) -> str:
        """Process Notion API operations based on the specified mode."""
        result = {}
        
        if mode == "list_databases":
            result = self.list_available_databases()
        elif mode == "create_page":
            result = self.create_page(
                page_title=kwargs.get("page_title"),
                database_name=kwargs.get("database_name"),
                parent_database_id=kwargs.get("parent_database_id"),
                parent_page_id=kwargs.get("parent_page_id"),
                properties_json=kwargs.get("properties_json"),
                content_blocks_json=kwargs.get("content_blocks_json")
            )
        elif mode == "query_db":
            result = self.query_database(
                database_name=kwargs.get("database_name"),
                database_id=kwargs.get("database_id"), 
                filter_json=kwargs.get("filter_json"),
                sorts_json=kwargs.get("sorts_json")
            )
        elif mode == "add_page_content":
            result = self.add_content_to_page(
                page_id=kwargs.get("page_id"),
                content_blocks_json=kwargs.get("content_blocks_json")
            )
        elif mode == "get_page_content":
            result = self.get_page_content(page_id=kwargs.get("page_id"))
        elif mode == "update_page_props":
            result = self.update_page_properties(
                page_id=kwargs.get("page_id"),
                properties_json=kwargs.get("properties_json")
            )
        else:
            result = {"error": True, "message": f"Invalid Notion tool mode: {mode}"}
        
        return json.dumps(result, ensure_ascii=False, indent=2)

    def __del__(self):
        if hasattr(self, 'client') and self.client:
            self.client.close() 
            