use serde::de::{self, Deserialize, Deserializer, SeqAccess, Visitor};
use serde::ser::{Serialize, SerializeTuple, Serializer};
use std::fmt;
use std::marker::PhantomData;

use super::FrozenFlattenedVecMap;

impl<K: Ord + PartialEq + Serialize, V: Serialize> Serialize for FrozenFlattenedVecMap<K, V> {
    fn serialize<S>(&self, serializer: S) -> Result<S::Ok, S::Error>
    where
        S: Serializer,
    {
        let mut tuple = serializer.serialize_tuple(3)?;

        tuple.serialize_element(&self.keys)?;
        tuple.serialize_element(&self.value_ranges)?;
        tuple.serialize_element(&self.flattened_values)?;

        tuple.end()
    }
}

impl<'de, K: Ord + PartialEq + Deserialize<'de>, V: Deserialize<'de>> Deserialize<'de>
    for FrozenFlattenedVecMap<K, V>
{
    fn deserialize<D>(deserializer: D) -> Result<Self, D::Error>
    where
        D: Deserializer<'de>,
    {
        struct FrozenFlattenedVecMapVisitor<K: Ord + PartialEq, V>(PhantomData<(K, V)>);

        impl<'de, K: Ord + PartialEq + Deserialize<'de>, V: Deserialize<'de>> Visitor<'de>
            for FrozenFlattenedVecMapVisitor<K, V>
        {
            type Value = FrozenFlattenedVecMap<K, V>;

            fn expecting(&self, formatter: &mut fmt::Formatter) -> fmt::Result {
                formatter.write_str("struct FrozenFlattenedVecMap")
            }

            fn visit_seq<S>(self, mut seq: S) -> Result<Self::Value, S::Error>
            where
                S: SeqAccess<'de>,
            {
                let keys = seq
                    .next_element()?
                    .ok_or_else(|| de::Error::invalid_length(0, &self))?;
                let value_ranges = seq
                    .next_element()?
                    .ok_or_else(|| de::Error::invalid_length(1, &self))?;
                let flattened_values = seq
                    .next_element()?
                    .ok_or_else(|| de::Error::invalid_length(2, &self))?;

                Ok(FrozenFlattenedVecMap {
                    keys,
                    value_ranges,
                    flattened_values,
                })
            }
        }

        deserializer.deserialize_tuple(3, FrozenFlattenedVecMapVisitor(PhantomData))
    }
}
