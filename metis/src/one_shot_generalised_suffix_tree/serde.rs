use serde::de::{self, Deserialize, Deserializer, SeqAccess, Visitor};
use serde::ser::{Serialize, SerializeTuple, Serializer};
use std::fmt;

use super::OneShotGeneralisedSuffixTree;

impl Serialize for OneShotGeneralisedSuffixTree {
    fn serialize<S>(&self, serializer: S) -> Result<S::Ok, S::Error>
    where
        S: Serializer,
    {
        let mut tuple = serializer.serialize_tuple(4)?;

        tuple.serialize_element(&self.nodes)?;
        tuple.serialize_element(&self.root_ref)?;
        tuple.serialize_element(&self.word)?;
        tuple.serialize_element(&self.word_starts)?;

        tuple.end()
    }
}

impl<'de> Deserialize<'de> for OneShotGeneralisedSuffixTree {
    fn deserialize<D>(deserializer: D) -> Result<Self, D::Error>
    where
        D: Deserializer<'de>,
    {
        struct OneShotGeneralisedSuffixTreeVisitor;

        impl<'de> Visitor<'de> for OneShotGeneralisedSuffixTreeVisitor {
            type Value = OneShotGeneralisedSuffixTree;

            fn expecting(&self, formatter: &mut fmt::Formatter) -> fmt::Result {
                formatter.write_str("struct OneShotGeneralisedSuffixTree")
            }

            fn visit_seq<V>(self, mut seq: V) -> Result<Self::Value, V::Error>
            where
                V: SeqAccess<'de>,
            {
                let nodes = seq
                    .next_element()?
                    .ok_or_else(|| de::Error::invalid_length(0, &self))?;
                let root_ref = seq
                    .next_element()?
                    .ok_or_else(|| de::Error::invalid_length(1, &self))?;
                let word = seq
                    .next_element()?
                    .ok_or_else(|| de::Error::invalid_length(2, &self))?;
                let word_starts = seq
                    .next_element()?
                    .ok_or_else(|| de::Error::invalid_length(3, &self))?;

                Ok(OneShotGeneralisedSuffixTree {
                    nodes,
                    root_ref,

                    word,
                    word_starts,
                })
            }
        }

        deserializer.deserialize_tuple(4, OneShotGeneralisedSuffixTreeVisitor)
    }
}
