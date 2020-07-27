use serde::de::{self, Deserialize, Deserializer, SeqAccess, Visitor};
use serde::ser::{Serialize, SerializeTuple, Serializer};
use std::fmt;
use std::iter::FromIterator;
use tinyset::SetUsize as TinySet;
use vec_map::VecMap;

use super::Node;

impl Serialize for Node {
    fn serialize<S>(&self, serializer: S) -> Result<S::Ok, S::Error>
    where
        S: Serializer,
    {
        let mut tuple = serializer.serialize_tuple(5)?;

        tuple.serialize_element(&self.index)?;
        tuple.serialize_element(&self.depth)?;
        tuple.serialize_element(&self.parent)?;
        tuple.serialize_element(&self.transition_links.iter().collect::<Vec<usize>>())?;
        tuple.serialize_element(
            &self
                .generalised_indices
                .iter()
                .map(|(key, value)| (key, value.iter().collect::<Vec<usize>>()))
                .collect::<Vec<(usize, Vec<usize>)>>(),
        )?;

        tuple.end()
    }
}

impl<'de> Deserialize<'de> for Node {
    fn deserialize<D>(deserializer: D) -> Result<Self, D::Error>
    where
        D: Deserializer<'de>,
    {
        struct NodeVisitor;

        impl<'de> Visitor<'de> for NodeVisitor {
            type Value = Node;

            fn expecting(&self, formatter: &mut fmt::Formatter) -> fmt::Result {
                formatter.write_str("struct Node")
            }

            fn visit_seq<V>(self, mut seq: V) -> Result<Self::Value, V::Error>
            where
                V: SeqAccess<'de>,
            {
                let index = seq
                    .next_element()?
                    .ok_or_else(|| de::Error::invalid_length(0, &self))?;
                let depth = seq
                    .next_element()?
                    .ok_or_else(|| de::Error::invalid_length(1, &self))?;
                let parent = seq
                    .next_element()?
                    .ok_or_else(|| de::Error::invalid_length(2, &self))?;
                let transition_links: Vec<usize> = seq
                    .next_element()?
                    .ok_or_else(|| de::Error::invalid_length(3, &self))?;
                let generalised_indices: Vec<(usize, Vec<usize>)> = seq
                    .next_element()?
                    .ok_or_else(|| de::Error::invalid_length(4, &self))?;

                Ok(Node {
                    index,
                    depth,
                    parent,
                    transition_links: TinySet::from_iter(transition_links.into_iter()),
                    generalised_indices: VecMap::from_iter(
                        generalised_indices
                            .into_iter()
                            .map(|(key, value)| (key, TinySet::from_iter(value.into_iter()))),
                    ),
                })
            }
        }

        deserializer.deserialize_tuple(5, NodeVisitor)
    }
}
