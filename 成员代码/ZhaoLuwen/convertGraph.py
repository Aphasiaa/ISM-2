import networkx as nx
import json
import numpy as np
from collections import defaultdict
import random
from datetime import datetime
import pandas as pd

def convert_time_to_timestamp(time_str):
    if not time_str:
        return 0
    try:
        dt = datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S")
        return dt.timestamp()
    except:
        return 0

def convert_gml_to_graphsage(gml_file, features_file, output_prefix, train_ratio=0.7, val_ratio=0.15):
    G = nx.read_gml(gml_file)
    
    with open(features_file, 'r') as f:
        node_features = json.load(f)
    
    nodes = list(G.nodes())
    id_map = {node: i for i, node in enumerate(nodes)}
    
    class_map = {}
    for node in nodes:
        node_type = G.nodes[node]['type']
        if node_type in ['fqdn', 'apex']:
            is_hijacked = G.nodes[node].get('hijacked', False)
            class_map[node] = 1 if is_hijacked else 0
        else:
            class_map[node] = -1
    
    num_nodes = len(nodes)
    feature_dim = 0
    features = {}
    
    for node in nodes:
        node_type = G.nodes[node]['type']
        if node_type == 'fqdn':
            features[node] = [
                float(G.nodes[node].get('count', 0)),
                convert_time_to_timestamp(G.nodes[node].get('last_seen', None))
            ]
        elif node_type == 'apex':
            features[node] = [
                float(G.nodes[node].get('count', 0)),
                convert_time_to_timestamp(G.nodes[node].get('last_seen', None))
            ]
        elif node_type == 'ns':
            features[node] = [
                float(G.nodes[node].get('count', 0)),
                convert_time_to_timestamp(G.nodes[node].get('last_seen', None))
            ]
        elif node_type == 'ip':
            features[node] = [
                float(G.nodes[node].get('count', 0)),
                convert_time_to_timestamp(G.nodes[node].get('last_seen', None))
            ]
        else:
            features[node] = [0.0, 0.0]
    
    feature_dim = len(features[nodes[0]])
    feats = np.zeros((num_nodes, feature_dim))
    for node, idx in id_map.items():
        feats[idx] = features[node]
    
    # 划分数据集
    domain_nodes = [node for node in nodes if G.nodes[node]['type'] in ['fqdn', 'apex']]
    random.shuffle(domain_nodes)
    train_size = int(len(domain_nodes) * train_ratio)
    val_size = int(len(domain_nodes) * val_ratio)
    
    train_nodes = domain_nodes[:train_size]
    val_nodes = domain_nodes[train_size:train_size + val_size]
    test_nodes = domain_nodes[train_size + val_size:]
    
    for node in nodes:
        G.nodes[node]['val'] = node in val_nodes
        G.nodes[node]['test'] = node in test_nodes
    
    # 保存结果文件
    graph_data = nx.node_link_data(G, edges="links")
    with open(f"{output_prefix}-G.json", 'w') as f:
        json.dump(graph_data, f)
    
    with open(f"{output_prefix}-id_map.json", 'w') as f:
        json.dump(id_map, f)
    
    with open(f"{output_prefix}-class_map.json", 'w') as f:
        json.dump(class_map, f)
    
    np.save(f"{output_prefix}-feats.npy", feats)
    
    # 保存为CSV格式
    nodes_data = []
    for node in nodes:
        node_type = G.nodes[node]['type']
        node_data = {
            'node_id': node,
            'feat_domain': 1 if node_type in ['fqdn', 'apex'] else 0,
            'feat_ip': 1 if node_type == 'ip' else 0,
            'feat_subnet': 1 if node_type == 'subnet' else 0,
            'label': class_map[node]
        }
        for i, feat in enumerate(features[node]):
            node_data[f'feat_{i}'] = feat
        nodes_data.append(node_data)
    
    nodes_df = pd.DataFrame(nodes_data)
    nodes_df.to_csv(f"{output_prefix}-nodes.csv", index=False)
    
    edges_data = []
    for u, v, data in G.edges(data=True):
        edge_type = data.get('relation', 'to')
        edge_data = {
            'source': u,
            'target': v,
            'edge_type': {
                'resolves_to': 0,
                'belongs_to': 1,
                'fqdnapex': 2,
                'similar_apex': 3,
                'similar_all': 4
            }.get(edge_type, 0)
        }
        edges_data.append(edge_data)
    
    edges_df = pd.DataFrame(edges_data)
    edges_df.to_csv(f"{output_prefix}-edges.csv", index=False)
    
    print(f"数据转换完成！输出文件前缀：{output_prefix}")
    print(f"节点数量：{num_nodes}")
    print(f"特征维度：{feature_dim}")
    print(f"域名节点数量：{len(domain_nodes)}")
    print(f"训练集大小：{len(train_nodes)}")
    print(f"验证集大小：{len(val_nodes)}")
    print(f"测试集大小：{len(test_nodes)}")
    print(f"被劫持域名数量：{sum(1 for node in domain_nodes if class_map[node] == 1)}")
    print(f"正常域名数量：{sum(1 for node in domain_nodes if class_map[node] == 0)}")

if __name__ == "__main__":
    # 使用示例
    gml_file = "your_graph.gml"
    features_file = "node_features.json"
    output_prefix = "graph_data"
    convert_gml_to_graphsage(gml_file, features_file, output_prefix) 