#!/usr/bin/env python3
"""
Ticket Management Lambda Function
Manages support tickets in DynamoDB with CRUD operations
"""

import json
import os
import boto3
from datetime import datetime
from typing import Dict, Any, Optional
from decimal import Decimal

# Initialize DynamoDB client
dynamodb = boto3.resource('dynamodb')
table_name = os.environ.get('TICKETS_TABLE', 'dev-customer-support-tickets')
table = dynamodb.Table(table_name)


def decimal_default(obj):
    """Convert Decimal to int/float for JSON serialization"""
    if isinstance(obj, Decimal):
        return float(obj) if obj % 1 else int(obj)
    raise TypeError


def generate_ticket_id() -> str:
    """Generate a unique ticket ID"""
    import uuid
    return f"TICKET-{uuid.uuid4().hex[:8].upper()}"


def create_ticket(event: Dict[str, Any]) -> Dict[str, Any]:
    """Create a new support ticket"""
    try:
        # Extract ticket data
        user_id = event.get('user_id') or event.get('customer_id') or 'anonymous'
        customer_email = event.get('customer_email') or event.get('email') or f"{user_id}@example.com"
        subject = event.get('subject') or event.get('title') or 'Support Request'
        description = event.get('description') or event.get('question') or event.get('message', '')
        category = event.get('category', 'general')
        priority = event.get('priority', 'medium')
        status = event.get('status', 'open')
        
        # Validate priority
        valid_priorities = ['critical', 'high', 'medium', 'low']
        if priority not in valid_priorities:
            priority = 'medium'
        
        # Validate category
        valid_categories = ['account', 'billing', 'technical', 'how-to', 'general']
        if category not in valid_categories:
            category = 'general'
        
        # Validate status
        valid_statuses = ['open', 'in-progress', 'resolved', 'closed', 'escalated', 'cancelled']
        if status not in valid_statuses:
            status = 'open'
        
        # Generate ticket ID
        ticket_id = generate_ticket_id()
        created_at = datetime.utcnow().isoformat()
        
        # Calculate estimated resolution time based on priority
        resolution_times = {
            'critical': '2 hours',
            'high': '24 hours',
            'medium': '48 hours',
            'low': '72 hours'
        }
        estimated_resolution = resolution_times.get(priority, '48 hours')
        
        # Create ticket item
        ticket_item = {
            'ticket_id': ticket_id,
            'customer_email': customer_email,
            'user_id': user_id,
            'subject': subject,
            'description': description,
            'category': category,
            'priority': priority,
            'status': status,
            'created_at': created_at,
            'updated_at': created_at,
            'estimated_resolution': estimated_resolution,
            'resolution_time': None,
            'assigned_to': None,
            'tags': event.get('tags', []),
            'metadata': event.get('metadata', {})
        }
        
        # Store in DynamoDB
        table.put_item(Item=ticket_item)
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'success': True,
                'ticket_id': ticket_id,
                'status': status,
                'priority': priority,
                'category': category,
                'created_at': created_at,
                'estimated_resolution': estimated_resolution,
                'message': f'Ticket {ticket_id} created successfully'
            }, default=decimal_default)
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({
                'success': False,
                'error': str(e),
                'message': 'Failed to create ticket'
            })
        }


def get_ticket(event: Dict[str, Any]) -> Dict[str, Any]:
    """Retrieve a ticket by ticket_id"""
    try:
        ticket_id = event.get('ticket_id')
        if not ticket_id:
            return {
                'statusCode': 400,
                'body': json.dumps({
                    'success': False,
                    'error': 'ticket_id is required'
                })
            }
        
        # Get ticket from DynamoDB
        response = table.get_item(Key={'ticket_id': ticket_id})
        
        if 'Item' not in response:
            return {
                'statusCode': 404,
                'body': json.dumps({
                    'success': False,
                    'error': f'Ticket {ticket_id} not found'
                })
            }
        
        ticket = response['Item']
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'success': True,
                'ticket': ticket
            }, default=decimal_default)
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({
                'success': False,
                'error': str(e),
                'message': 'Failed to retrieve ticket'
            })
        }


def update_ticket_status(event: Dict[str, Any]) -> Dict[str, Any]:
    """Update ticket status"""
    try:
        ticket_id = event.get('ticket_id')
        new_status = event.get('status')
        
        if not ticket_id:
            return {
                'statusCode': 400,
                'body': json.dumps({
                    'success': False,
                    'error': 'ticket_id is required'
                })
            }
        
        if not new_status:
            return {
                'statusCode': 400,
                'body': json.dumps({
                    'success': False,
                    'error': 'status is required'
                })
            }
        
        # Validate status
        valid_statuses = ['open', 'in-progress', 'resolved', 'closed', 'escalated', 'cancelled']
        if new_status not in valid_statuses:
            return {
                'statusCode': 400,
                'body': json.dumps({
                    'success': False,
                    'error': f'Invalid status. Must be one of: {valid_statuses}'
                })
            }
        
        # Update ticket
        updated_at = datetime.utcnow().isoformat()
        
        update_expression = "SET #status = :status, updated_at = :updated_at"
        expression_attribute_names = {'#status': 'status'}
        expression_attribute_values = {
            ':status': new_status,
            ':updated_at': updated_at
        }
        
        # If status is resolved or closed, set resolution_time
        if new_status in ['resolved', 'closed']:
            update_expression += ", resolution_time = :resolution_time"
            expression_attribute_values[':resolution_time'] = updated_at
        
        table.update_item(
            Key={'ticket_id': ticket_id},
            UpdateExpression=update_expression,
            ExpressionAttributeNames=expression_attribute_names,
            ExpressionAttributeValues=expression_attribute_values,
            ReturnValues='ALL_NEW'
        )
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'success': True,
                'ticket_id': ticket_id,
                'status': new_status,
                'updated_at': updated_at,
                'message': f'Ticket {ticket_id} status updated to {new_status}'
            }, default=decimal_default)
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({
                'success': False,
                'error': str(e),
                'message': 'Failed to update ticket status'
            })
        }


def list_tickets(event: Dict[str, Any]) -> Dict[str, Any]:
    """List tickets by customer_email, status, or priority"""
    try:
        customer_email = event.get('customer_email') or event.get('email')
        status = event.get('status')
        priority = event.get('priority')
        limit = int(event.get('limit', 10))
        
        # Use appropriate index
        if customer_email:
            # Query by customer_email
            response = table.query(
                IndexName='customer-email-index',
                KeyConditionExpression='customer_email = :email',
                ExpressionAttributeValues={':email': customer_email},
                Limit=limit,
                ScanIndexForward=False  # Most recent first
            )
        elif status:
            # Query by status
            response = table.query(
                IndexName='status-index',
                KeyConditionExpression='#status = :status',
                ExpressionAttributeNames={'#status': 'status'},
                ExpressionAttributeValues={':status': status},
                Limit=limit,
                ScanIndexForward=False
            )
        elif priority:
            # Query by priority
            response = table.query(
                IndexName='priority-index',
                KeyConditionExpression='priority = :priority',
                ExpressionAttributeValues={':priority': priority},
                Limit=limit,
                ScanIndexForward=False
            )
        else:
            # Scan all tickets (limited)
            response = table.scan(Limit=limit)
        
        tickets = response.get('Items', [])
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'success': True,
                'tickets': tickets,
                'count': len(tickets)
            }, default=decimal_default)
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({
                'success': False,
                'error': str(e),
                'message': 'Failed to list tickets'
            })
        }


def lambda_handler(event: Dict[str, Any], context) -> Dict[str, Any]:
    """
    Lambda function handler for ticket management
    Supports multiple operations: create, get, update_status, list
    """
    # Log the raw event to see what AgentCore Gateway is sending
    print("=" * 80)
    print("RAW_EVENT:", json.dumps(event, default=str, indent=2))
    print("=" * 80)
    
    try:
        # Determine operation from Gateway tool name (preferred) or event
        operation = None
        
        # Check if invoked by AgentCore Gateway (has context with tool name)
        # Log context information for debugging
        if context:
            print(f"DEBUG: Context type: {type(context)}")
            if hasattr(context, 'client_context'):
                print(f"DEBUG: client_context exists: {context.client_context}")
                if context.client_context:
                    if hasattr(context.client_context, 'custom'):
                        print(f"DEBUG: client_context.custom exists: {context.client_context.custom}")
                        if context.client_context.custom:
                            tool_name = context.client_context.custom.get("bedrockAgentCoreToolName")
                            print(f"DEBUG: bedrockAgentCoreToolName from context: {tool_name}")
                            if tool_name:
                                # Tool name format: target_name___tool_name
                                # Extract the tool name after ___
                                if "___" in tool_name:
                                    tool = tool_name.split("___")[1]
                                    print(f"DEBUG: Gateway tool name: {tool_name}, extracted tool: {tool}")
                                    # Map tool names to operations
                                    tool_to_operation = {
                                        "create_ticket": "create",
                                        "get_ticket": "get",
                                        "update_ticket": "update_status",
                                        "list_tickets": "list"
                                    }
                                    operation = tool_to_operation.get(tool)
                                    if operation:
                                        print(f"DEBUG: Mapped tool '{tool}' to operation '{operation}'")
            else:
                print(f"DEBUG: context.client_context does not exist")
        
        # Fallback: Extract operation from event (for direct invocation or backward compatibility)
        if not operation:
            operation = event.get('operation') or event.get('action')
            print(f"DEBUG: Extracted operation from event = {operation}")
            
            # If no operation specified, try to infer from event structure
            # IMPORTANT: Check for create indicators FIRST (subject, description) before list indicators
            if not operation:
                if 'subject' in event or 'description' in event or 'question' in event:
                    operation = 'create'
                elif 'ticket_id' in event and 'status' in event:
                    operation = 'update_status'
                elif 'ticket_id' in event:
                    operation = 'get'
                elif 'customer_email' in event or ('status' in event and 'priority' not in event):
                    operation = 'list'
                else:
                    operation = 'list'  # Default to list if unclear
        
        # Route to appropriate handler
        print(f"DEBUG: Routing to handler for operation: {operation}")
        if operation == 'create':
            result = create_ticket(event)
            print(f"DEBUG: create_ticket result: {json.dumps(result, default=str)}")
            return result
        elif operation == 'get':
            result = get_ticket(event)
            print(f"DEBUG: get_ticket result: {json.dumps(result, default=str)}")
            return result
        elif operation == 'update_status' or operation == 'update':
            result = update_ticket_status(event)
            print(f"DEBUG: update_ticket_status result: {json.dumps(result, default=str)}")
            return result
        elif operation == 'list':
            result = list_tickets(event)
            print(f"DEBUG: list_tickets result: {json.dumps(result, default=str)}")
            return result
        else:
            return {
                'statusCode': 400,
                'body': json.dumps({
                    'success': False,
                    'error': f'Unknown operation: {operation}',
                    'supported_operations': ['create', 'get', 'update_status', 'list']
                })
            }
            
    except Exception as e:
        import traceback
        error_traceback = traceback.format_exc()
        print("=" * 80)
        print("ERROR in lambda_handler:")
        print(f"Exception: {str(e)}")
        print(f"Traceback:\n{error_traceback}")
        print("=" * 80)
        return {
            'statusCode': 500,
            'body': json.dumps({
                'success': False,
                'error': str(e),
                'message': 'Internal server error'
            })
        }


# For local testing
if __name__ == "__main__":
    # Test create
    test_event = {
        'operation': 'create',
        'user_id': 'test-user-123',
        'customer_email': 'test@example.com',
        'subject': 'Password reset issue',
        'description': 'I cannot reset my password',
        'category': 'account',
        'priority': 'high'
    }
    
    result = lambda_handler(test_event, None)
    print(json.dumps(result, indent=2, default=decimal_default))

